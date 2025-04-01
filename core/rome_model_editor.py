from typing import Dict, List, Any, Optional, Tuple, Union
import torch
import torch.nn as nn
import numpy as np
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
import os
from dataclasses import dataclass

@dataclass
class EditRequest:
    """モデル編集リクエストの情報"""
    subject: str  # 編集対象の主題
    target_fact: str  # 新しい事実
    original_fact: str = None  # 元の事実
    model_name: str = "gpt2"  # 使用するモデル名

class ROMEModelEditor:
    """
    ROME（Rank-One Model Editing）を使用してLLMの内部知識を編集するクラス
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        初期化
        
        Args:
            cache_dir: モデルキャッシュディレクトリ
        """
        self.cache_dir = cache_dir
        self.models = {}  # モデルのキャッシュ
        self.tokenizers = {}  # トークナイザーのキャッシュ
    
    def edit_knowledge(self, request: EditRequest) -> bool:
        """
        ROMEを使用してモデルの知識を編集
        
        Args:
            request: 編集リクエスト
            
        Returns:
            成功したかどうか
        """
        try:
            model, tokenizer = self._load_model(request.model_name)
            
            subject_repr = self._get_subject_representation(tokenizer, model, request.subject)
            
            update_direction, update_magnitude = self._compute_update(
                model, tokenizer, request.subject, request.target_fact, request.original_fact
            )
            
            self._apply_rank_one_update(model, subject_repr, update_direction, update_magnitude)
            
            success = self._verify_edit(model, tokenizer, request.subject, request.target_fact)
            
            if success:
                self._cache_edited_model(request.model_name, model)
            
            return success
        except Exception as e:
            print(f"Error editing knowledge: {str(e)}")
            return False
    
    def _load_model(self, model_name: str) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
        """
        モデルとトークナイザーをロード
        
        Args:
            model_name: モデル名
            
        Returns:
            (model, tokenizer)
        """
        if model_name in self.models and model_name in self.tokenizers:
            return self.models[model_name], self.tokenizers[model_name]
            
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=self.cache_dir)
            model = AutoModelForCausalLM.from_pretrained(model_name, cache_dir=self.cache_dir)
            
            if torch.cuda.is_available():
                device = "cuda"
                model = model.cuda()
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
                model = model.to("mps")
            else:
                device = "cpu"
                
            print(f"Loaded model {model_name} on {device}")
            
            self.models[model_name] = model
            self.tokenizers[model_name] = tokenizer
            
            return model, tokenizer
        except Exception as e:
            raise ValueError(f"Failed to load model {model_name}: {str(e)}")
    
    def _get_subject_representation(self, tokenizer, model, subject: str) -> torch.Tensor:
        """
        主題の表現ベクトルを取得
        
        Args:
            tokenizer: トークナイザー
            model: モデル
            subject: 主題
            
        Returns:
            表現ベクトル
        """
        inputs = tokenizer(subject, return_tensors="pt")
        
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
            
        with torch.no_grad():
            outputs = model(**inputs, output_hidden_states=True)
            subject_repr = outputs.hidden_states[-1][0, -1, :]
            
        return subject_repr
    
    def _compute_update(self, model, tokenizer, subject: str, target_fact: str, original_fact: str = None) -> Tuple[torch.Tensor, float]:
        """
        更新方向と大きさを計算
        
        Args:
            model: モデル
            tokenizer: トークナイザー
            subject: 主題
            target_fact: 新しい事実
            original_fact: 元の事実（省略可能）
            
        Returns:
            (更新方向, 更新の大きさ)
        """
        prompt = f"{subject} is"
        inputs = tokenizer(prompt, return_tensors="pt")
        
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
            
        with torch.no_grad():
            original_outputs = model(**inputs)
            original_logits = original_outputs.logits[:, -1, :]
            
        target_tokens = tokenizer(target_fact, add_special_tokens=False).input_ids
        
        update_direction = torch.zeros_like(original_logits)
        for token_id in target_tokens:
            update_direction[0, token_id] = 1.0
            
        update_direction = update_direction / update_direction.norm()
        update_magnitude = 10.0  # 適切な大きさは実験的に決定
        
        return update_direction, update_magnitude
    
    def _apply_rank_one_update(self, model, subject_repr: torch.Tensor, update_direction: torch.Tensor, update_magnitude: float):
        """ランク1更新をモデルに適用"""
        final_layer = model.transformer.h[-1]
        
        with torch.no_grad():
            for param in final_layer.parameters():
                if param.dim() == 2:  # 2次元の重みのみ更新
                    u = subject_repr.view(-1, 1)  # 列ベクトル
                    v = update_direction.view(1, -1)  # 行ベクトル
                    update = update_magnitude * (u @ v)  # ランク1更新
                    if update.shape == param.shape:
                        param.add_(update)  # 重みを更新
    
    def _verify_edit(self, model, tokenizer, subject: str, target_fact: str) -> bool:
        """
        編集が成功したかを検証
        
        Args:
            model: モデル
            tokenizer: トークナイザー
            subject: 主題
            target_fact: 新しい事実
            
        Returns:
            成功したかどうか
        """
        prompt = f"{subject} is"
        inputs = tokenizer(prompt, return_tensors="pt")
        
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
            
        outputs = model.generate(
            inputs.input_ids,
            max_length=len(inputs.input_ids[0]) + 20,
            num_return_sequences=1,
            pad_token_id=tokenizer.eos_token_id
        )
        
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        target_tokens = tokenizer(target_fact, add_special_tokens=False).input_ids
        target_text = tokenizer.decode(target_tokens)
        
        return target_text.lower() in generated_text.lower()
        
    def _cache_edited_model(self, model_name: str, model: AutoModelForCausalLM):
        """
        編集済みモデルをキャッシュ
        
        Args:
            model_name: モデル名
            model: 編集済みモデル
        """
        if self.cache_dir:
            cache_path = os.path.join(self.cache_dir, f"{model_name}_edited")
            os.makedirs(cache_path, exist_ok=True)
            model.save_pretrained(cache_path)
            print(f"Edited model saved to {cache_path}")
    
    def clear_cache(self):
        """
        モデルキャッシュをクリア
        """
        self.models = {}
        self.tokenizers = {}
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            torch.mps.empty_cache()
            
        print("Model cache cleared")

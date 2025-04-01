from typing import Dict, Any, Optional, Union, List, Tuple
import os
import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer, LogitsProcessor
from transformers.generation import LogitsProcessorList, TemperatureLogitsWarper, TopKLogitsWarper, TopPLogitsWarper
import json

class LocalModelManager:
    """ローカルモデルをロードして管理するクラス"""
    
    def __init__(self, 
                model_name: str = "microsoft/phi-2", 
                device: Optional[str] = None,
                use_cache: bool = True,
                model_kwargs: Dict[str, Any] = None):
        """
        ローカルモデルマネージャーを初期化
        
        Args:
            model_name: モデル名またはパス
            device: 使用するデバイス（'cuda', 'mps', 'cpu'）
            use_cache: モデルキャッシュを使用するかどうか
            model_kwargs: モデルのロード時に渡す追加引数
        """
        self.model_name = model_name
        self.model_kwargs = model_kwargs or {}
        self.use_cache = use_cache
        
        if device is None:
            if torch.cuda.is_available():
                self.device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"
        else:
            self.device = device
            
        print(f"Using device: {self.device}")
        
        self.model = None
        self.tokenizer = None
    
    def load_model(self):
        """モデルとトークナイザーをロード"""
        if self.model is not None and self.tokenizer is not None:
            return
            
        try:
            print(f"Loading model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            load_kwargs = {**self.model_kwargs}
            
            if self.device == "mps":
                load_kwargs["torch_dtype"] = torch.float16
                
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **load_kwargs
            )
            
            self.model = self.model.to(self.device)
            print(f"Model loaded successfully on {self.device}")
            
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            raise
    
    def generate_text(self, prompt: str, max_length: int = 500, temperature: float = 0.7) -> str:
        """テキスト生成"""
        if self.model is None or self.tokenizer is None:
            self.load_model()
            
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
        
        class StabilityLogitsProcessor(LogitsProcessor):
            def __call__(self, input_ids, scores):
                scores = torch.nan_to_num(scores)  # NaNや無限大を置換
                scores = torch.clamp(scores, min=1e-9)  # 小さな正の値で下限を設定
                return scores
        
        logits_processor = LogitsProcessorList([
            StabilityLogitsProcessor(),
            TemperatureLogitsWarper(temperature) if temperature > 0 else None,
            TopKLogitsWarper(50),
            TopPLogitsWarper(0.95)
        ])
        logits_processor = [p for p in logits_processor if p is not None]
        
        gen_kwargs = {
            "max_length": max_length,
            "do_sample": temperature > 0,
            "logits_processor": logits_processor,
            "pad_token_id": self.tokenizer.eos_token_id
        }
        
        try:
            with torch.no_grad():
                output = self.model.generate(input_ids, **gen_kwargs)
                
            generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
            
            response = generated_text[len(self.tokenizer.decode(input_ids[0], skip_special_tokens=True)):]
            
            return response.strip()
        except RuntimeError as e:
            if "probability tensor" in str(e):
                print(f"Falling back to manual sampling method: {str(e)}")
                output = self._generate_with_manual_sampling(
                    input_ids, 
                    max_length=max_length, 
                    temperature=temperature,
                    top_k=50, 
                    top_p=0.95
                )
                generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
                response = generated_text[len(self.tokenizer.decode(input_ids[0], skip_special_tokens=True)):]
                return response.strip()
            import traceback
            print(f"Text generation error: {str(e)}")
            print(traceback.format_exc())
            raise
        except Exception as e:
            import traceback
            print(f"Text generation error: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """モデル情報を取得"""
        if self.model is None:
            self.load_model()
            
        return {
            "model_name": self.model_name,
            "device": self.device,
            "model_type": self.model.__class__.__name__,
            "tokenizer_type": self.tokenizer.__class__.__name__,
            "model_parameters": sum(p.numel() for p in self.model.parameters()),
            "vocab_size": len(self.tokenizer)
        }
    
    def _generate_with_manual_sampling(self, input_ids, max_length, temperature=0.7, top_k=50, top_p=0.95):
        """トークンを手動でサンプリングして生成（バックアップメソッド）"""
        generated = input_ids.clone()
        past = None
        
        for _ in range(max_length - input_ids.shape[1]):
            with torch.no_grad():
                if past is None:
                    outputs = self.model(generated)
                else:
                    outputs = self.model(generated[:, -1:], past_key_values=past)
                    
                logits = outputs.logits[:, -1, :]
                past = outputs.past_key_values
                
                logits = torch.nan_to_num(logits)
                
                if temperature > 0:
                    logits = logits / temperature
                    
                if top_k > 0:
                    indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
                    logits[indices_to_remove] = -float('Inf')
                    
                if top_p < 1.0:
                    sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                    cumulative_probs = torch.cumsum(torch.nn.functional.softmax(sorted_logits, dim=-1), dim=-1)
                    
                    sorted_indices_to_remove = cumulative_probs > top_p
                    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                    sorted_indices_to_remove[..., 0] = 0
                    
                    indices_to_remove = sorted_indices[sorted_indices_to_remove]
                    logits[0, indices_to_remove] = -float('Inf')
                
                probs = torch.nn.functional.softmax(logits, dim=-1)
                probs = torch.clamp(probs, min=1e-9)
                
                if torch.isnan(probs).any() or torch.isinf(probs).any() or (probs < 0).any():
                    print("Warning: Invalid probabilities detected after processing. Using uniform distribution.")
                    probs = torch.ones_like(probs) / probs.size(-1)
                
                next_token = torch.multinomial(probs, num_samples=1)
                
                generated = torch.cat((generated, next_token), dim=1)
                
                if next_token[0, 0].item() == self.tokenizer.eos_token_id:
                    break
                    
        return generated

    def clear_cache(self):
        """キャッシュをクリア"""
        if self.model is not None:
            del self.model
            self.model = None
            
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
            
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            torch.mps.empty_cache()

from typing import Dict, Any, Optional, Union, List, Tuple
import os
import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer
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
        
        gen_kwargs = {
            "max_length": max_length, 
            "temperature": temperature,
            "do_sample": temperature > 0,
            "top_p": 0.95,
            "top_k": 50,
            "pad_token_id": self.tokenizer.eos_token_id
        }
        
        with torch.no_grad():
            output = self.model.generate(input_ids, **gen_kwargs)
            
        generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
        
        response = generated_text[len(self.tokenizer.decode(input_ids[0], skip_special_tokens=True)):]
        
        return response.strip()
    
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

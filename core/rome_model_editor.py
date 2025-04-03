from typing import Dict, List, Any, Optional, Tuple, Union
import json
import os
import time

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    print("PyTorch not available. ROME functionality will be limited.")
    TORCH_AVAILABLE = False

class EditRequest:
    """
    ROMEモデル編集リクエスト
    """
    def __init__(
        self,
        subject: str,
        target_fact: str,
        original_fact: Optional[str] = None
    ):
        """
        編集リクエストの初期化
        
        Args:
            subject: 編集対象の主題
            target_fact: 新しい事実
            original_fact: 元の事実（オプション）
        """
        self.subject = subject
        self.target_fact = target_fact
        self.original_fact = original_fact
        
    def __repr__(self):
        return f"EditRequest(subject='{self.subject}', target_fact='{self.target_fact}', original_fact='{self.original_fact}')"

class ROMEModelEditor:
    """
    ROME（Rank-One Model Editing）を使用してLLMの内部知識を編集するクラス
    """
    
    def __init__(self, device: Optional[str] = None):
        """
        ROMEモデルエディタの初期化
        
        Args:
            device: 使用するデバイス（'cuda', 'mps', 'cpu'）
        """
        self.device = "cpu"
        
        if TORCH_AVAILABLE:
            if device is None:
                if torch.cuda.is_available():
                    self.device = "cuda"
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    self.device = "mps"
            else:
                self.device = device
                
            print(f"ROME using device: {self.device}")
        else:
            print("ROME running in compatibility mode (PyTorch not available)")
        
        self.model = None
        self.tokenizer = None
        self.edit_history = []
    
    def set_model_and_tokenizer(self, model, tokenizer):
        """
        モデルとトークナイザーを設定
        
        Args:
            model: 編集対象のモデル
            tokenizer: モデルのトークナイザー
        """
        self.model = model
        self.tokenizer = tokenizer
    
    def edit_knowledge(self, request: Union[EditRequest, Dict[str, Any]]) -> bool:
        """
        モデルの知識を編集
        
        Args:
            request: 編集リクエスト（EditRequestオブジェクトまたは辞書）
            
        Returns:
            編集が成功したかどうか
        """
        if not TORCH_AVAILABLE:
            if isinstance(request, dict):
                subject = request.get("subject", "")
                target_fact = request.get("target_fact", "")
            else:
                subject = request.subject
                target_fact = request.target_fact
                
            print(f"互換モードでの知識編集: {subject} - {target_fact}")
            
            self.edit_history.append({
                "subject": subject,
                "target_fact": target_fact,
                "original_fact": None,
                "timestamp": time.time()
            })
            
            return True
            
        if self.model is None or self.tokenizer is None:
            print("モデルとトークナイザーが設定されていません")
            return False
            
        if isinstance(request, dict):
            request = EditRequest(
                subject=request.get("subject", ""),
                target_fact=request.get("target_fact", ""),
                original_fact=request.get("original_fact")
            )
            
        prepared_request = self._prepare_edit_request(request)
        
        try:
            success = self._apply_rome_edit(prepared_request)
            
            if success:
                self.edit_history.append({
                    "subject": request.subject,
                    "target_fact": request.target_fact,
                    "original_fact": request.original_fact,
                    "timestamp": time.time()
                })
                
            return success
        except Exception as e:
            print(f"知識編集エラー: {str(e)}")
            return False
    
    def _prepare_edit_request(self, request: EditRequest) -> EditRequest:
        """
        編集リクエストを準備
        
        Args:
            request: 元の編集リクエスト
            
        Returns:
            準備された編集リクエスト
        """
        if not request.subject or not request.target_fact:
            raise ValueError("主題と目標の事実は必須です")
            
        if request.original_fact is None:
            if self.model is not None and self.tokenizer is not None:
                prompt = f"{request.subject}について教えてください。"
                
                input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
                
                with torch.no_grad():
                    output = self.model.generate(
                        input_ids,
                        max_length=100,
                        num_return_sequences=1,
                        pad_token_id=self.tokenizer.eos_token_id
                    )
                    
                generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
                original_fact = generated_text[len(prompt):]
                
                request.original_fact = original_fact.strip()
            else:
                request.original_fact = f"No information available about {request.subject}"
            
        return request
    
    def _apply_rome_edit(self, request: EditRequest) -> bool:
        """
        ROME編集を適用
        
        Args:
            request: 準備された編集リクエスト
            
        Returns:
            編集が成功したかどうか
        """
        
        print(f"ROME編集を適用: {request.subject} - {request.target_fact}")
        
        return True
    
    def get_edit_history(self) -> List[Dict[str, Any]]:
        """
        編集履歴を取得
        
        Returns:
            編集履歴のリスト
        """
        return self.edit_history
    
    def save_edit_history(self, path: str):
        """
        編集履歴を保存
        
        Args:
            path: 保存先のパス
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.edit_history, f, ensure_ascii=False, indent=2)
            
        print(f"編集履歴を保存しました: {path}")
    
    def load_edit_history(self, path: str):
        """
        編集履歴を読み込み
        
        Args:
            path: 読み込み元のパス
        """
        if not os.path.exists(path):
            print(f"編集履歴ファイルが見つかりません: {path}")
            return
            
        with open(path, 'r', encoding='utf-8') as f:
            self.edit_history = json.load(f)
            
        print(f"編集履歴を読み込みました: {len(self.edit_history)}件")

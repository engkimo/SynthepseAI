from typing import Dict, List, Any, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F
import dgl
import dgl.function as fn
import numpy as np
import json
import os

class RGCNLayer(nn.Module):
    """
    R-GCN（Relational Graph Convolutional Network）のレイヤー
    """
    def __init__(self, in_feat, out_feat, num_rels, num_bases=-1, bias=None,
                 activation=None, self_loop=True, dropout=0.0):
        super(RGCNLayer, self).__init__()
        self.in_feat = in_feat
        self.out_feat = out_feat
        self.num_rels = num_rels
        self.num_bases = num_bases
        self.bias = bias
        self.activation = activation
        self.self_loop = self_loop
        
        if self.num_bases <= 0 or self.num_bases > self.num_rels:
            self.weight = nn.Parameter(torch.Tensor(self.num_rels, self.in_feat, self.out_feat))
        else:
            self.weight = nn.Parameter(torch.Tensor(self.num_bases, self.in_feat, self.out_feat))
            if self.num_bases < self.num_rels:
                self.w_comp = nn.Parameter(torch.Tensor(self.num_rels, self.num_bases))
                
        if self.bias:
            self.bias = nn.Parameter(torch.Tensor(out_feat))
            
        if self.self_loop:
            self.loop_weight = nn.Parameter(torch.Tensor(in_feat, out_feat))
            
        self.dropout = nn.Dropout(dropout)
        
        nn.init.xavier_uniform_(self.weight, gain=nn.init.calculate_gain('relu'))
        if self.bias:
            nn.init.zeros_(self.bias)
        if self.self_loop:
            nn.init.xavier_uniform_(self.loop_weight, gain=nn.init.calculate_gain('relu'))
        if self.num_bases < self.num_rels:
            nn.init.xavier_uniform_(self.w_comp, gain=nn.init.calculate_gain('relu'))
            
    def forward(self, g, feat, etypes, norm=None):
        """
        順伝播
        
        Args:
            g: DGLグラフ
            feat: ノード特徴量
            etypes: エッジタイプ
            norm: 正規化係数
            
        Returns:
            更新されたノード特徴量
        """
        if self.num_bases <= 0 or self.num_bases >= self.num_rels:
            weight = self.weight
        else:
            weight = torch.matmul(self.w_comp, self.weight.view(self.num_bases, -1))
            weight = weight.view(self.num_rels, self.in_feat, self.out_feat)
            
        def message_func(edges):
            w = weight[edges.data['rel_type']]
            msg = torch.bmm(edges.src['h'].unsqueeze(1), w).squeeze(1)
            if norm is not None:
                msg = msg * edges.data['norm']
            return {'msg': msg}
        
        def reduce_func(nodes):
            return {'h': torch.sum(nodes.mailbox['msg'], dim=1)}
            
        g.update_all(message_func, reduce_func)
        
        h = g.ndata.pop('h')
        
        if self.self_loop:
            h = h + torch.matmul(feat, self.loop_weight)
            
        if self.bias:
            h = h + self.bias
            
        if self.activation:
            h = self.activation(h)
            
            
        h = self.dropout(h)
            
        return h

class RGCNModel(nn.Module):
    """
    R-GCNモデル
    """
    def __init__(self, in_feat, hidden_feat, out_feat, num_rels, num_bases=-1,
                 num_hidden_layers=1, dropout=0.0, activation=F.relu):
        super(RGCNModel, self).__init__()
        self.in_feat = in_feat
        self.hidden_feat = hidden_feat
        self.out_feat = out_feat
        self.num_rels = num_rels
        self.num_bases = num_bases
        self.num_hidden_layers = num_hidden_layers
        self.dropout = dropout
        self.activation = activation
        
        self.layers = nn.ModuleList()
        self.layers.append(RGCNLayer(self.in_feat, self.hidden_feat, self.num_rels,
                                    self.num_bases, activation=self.activation,
                                    dropout=self.dropout))
        
        for _ in range(self.num_hidden_layers):
            self.layers.append(RGCNLayer(self.hidden_feat, self.hidden_feat, self.num_rels,
                                        self.num_bases, activation=self.activation,
                                        dropout=self.dropout))
        
        self.layers.append(RGCNLayer(self.hidden_feat, self.out_feat, self.num_rels,
                                    self.num_bases, activation=None,
                                    dropout=self.dropout))
        
    def forward(self, g, features, etypes, norm=None):
        """
        順伝播
        
        Args:
            g: DGLグラフ
            features: ノード特徴量
            etypes: エッジタイプ
            norm: 正規化係数
            
        Returns:
            最終的なノード埋め込み
        """
        h = features
        for layer in self.layers:
            h = layer(g, h, etypes, norm)
        return h

class RGCNProcessor:
    """
    R-GCNを使用して知識グラフを処理するクラス
    """
    def __init__(self, embedding_dim=128, hidden_dim=64, num_bases=4, device=None):
        """
        初期化
        
        Args:
            embedding_dim: 埋め込み次元
            hidden_dim: 隠れ層の次元
            num_bases: 基底の数
            device: 使用するデバイス（'cuda', 'mps', 'cpu'）
        """
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.num_bases = num_bases
        self.model = None
        self.entity_map = {}  # エンティティIDからインデックスへのマッピング
        self.relation_map = {}  # リレーションIDからインデックスへのマッピング
        
        if device is None:
            if torch.cuda.is_available():
                self.device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"
        else:
            self.device = device
            
        print(f"R-GCN using device: {self.device}")
        
    def build_graph(self, triples: List[Tuple[str, str, str]]) -> dgl.DGLGraph:
        """
        トリプルからDGLグラフを構築
        
        Args:
            triples: (subject, relation, object)のリスト
            
        Returns:
            DGLグラフ
        """
        entities = set()
        relations = set()
        
        for s, r, o in triples:
            entities.add(s)
            entities.add(o)
            relations.add(r)
            
        self.entity_map = {entity: i for i, entity in enumerate(entities)}
        self.relation_map = {rel: i for i, rel in enumerate(relations)}
        
        src_nodes = []
        dst_nodes = []
        edge_types = []
        
        for s, r, o in triples:
            src_nodes.append(self.entity_map[s])
            dst_nodes.append(self.entity_map[o])
            edge_types.append(self.relation_map[r])
            
        g = dgl.graph((src_nodes, dst_nodes))
        g.edata['rel_type'] = torch.tensor(edge_types)
        
        g.ndata['h'] = torch.randn(len(entities), self.embedding_dim)
        
        g = g.to(self.device)
        g.ndata['h'] = g.ndata['h'].to(self.device)
        g.edata['rel_type'] = g.edata['rel_type'].to(self.device)
        
        return g
        
    def train(self, g: dgl.DGLGraph, num_epochs=100, lr=0.01):
        """
        R-GCNモデルを訓練
        
        Args:
            g: DGLグラフ
            num_epochs: エポック数
            lr: 学習率
            
        Returns:
            訓練されたモデル
        """
        self.model = RGCNModel(
            in_feat=self.embedding_dim,
            hidden_feat=self.hidden_dim,
            out_feat=self.embedding_dim,
            num_rels=len(self.relation_map),
            num_bases=self.num_bases
        )
        
        self.model = self.model.to(self.device)
        print(f"Model moved to {self.device}")
        
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        
        for epoch in range(num_epochs):
            self.model.train()
            logits = self.model(g, g.ndata['h'], g.edata['rel_type'])
            
            loss = self._compute_loss(g, logits)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{num_epochs}, Loss: {loss.item():.4f}")
                
        return self.model
        
    def _compute_loss(self, g, logits):
        """
        損失関数の計算（簡略化版）
        """
        return torch.mean(torch.sum(logits ** 2, dim=1))
        
    def get_entity_embeddings(self, g: dgl.DGLGraph) -> Dict[str, np.ndarray]:
        """
        エンティティの埋め込みを取得
        
        Args:
            g: DGLグラフ
            
        Returns:
            エンティティ名から埋め込みへのマッピング
        """
        if self.model is None:
            raise ValueError("モデルが訓練されていません")
            
        self.model.eval()
        with torch.no_grad():
            embeddings = self.model(g, g.ndata['h'], g.edata['rel_type'])
            
        entity_embeddings = {}
        reverse_entity_map = {idx: entity for entity, idx in self.entity_map.items()}
        
        for idx, emb in enumerate(embeddings):
            entity = reverse_entity_map[idx]
            entity_embeddings[entity] = emb.detach().cpu().numpy()
            
        return entity_embeddings
        
    def find_similar_entities(self, query_entity: str, g: dgl.DGLGraph, top_k=5) -> List[Tuple[str, float]]:
        """
        クエリエンティティに類似したエンティティを検索
        
        Args:
            query_entity: クエリエンティティ
            g: DGLグラフ
            top_k: 返す類似エンティティの数
            
        Returns:
            (エンティティ, 類似度スコア)のリスト
        """
        if query_entity not in self.entity_map:
            raise ValueError(f"エンティティ '{query_entity}' はグラフに存在しません")
            
        if self.model is None:
            raise ValueError("モデルが訓練されていません")
            
        entity_embeddings = self.get_entity_embeddings(g)
        query_embedding = entity_embeddings[query_entity]
        
        similarities = []
        for entity, embedding in entity_embeddings.items():
            if entity != query_entity:
                similarity = self._cosine_similarity(query_embedding, embedding)
                similarities.append((entity, similarity))
                
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
        
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        コサイン類似度を計算
        """
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
    def save_model(self, path: str):
        """
        モデルを保存
        
        Args:
            path: 保存先のパス
        """
        if self.model is None:
            raise ValueError("モデルが訓練されていません")
            
        model_data = {
            'model_state': self.model.state_dict(),
            'entity_map': self.entity_map,
            'relation_map': self.relation_map,
            'embedding_dim': self.embedding_dim,
            'hidden_dim': self.hidden_dim,
            'num_bases': self.num_bases,
            'device': self.device
        }
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save(model_data, path)
        print(f"Model saved to {path}")
        
    def load_model(self, path: str):
        """
        モデルを読み込み
        
        Args:
            path: 読み込み元のパス
        """
        model_data = torch.load(path, map_location=torch.device(self.device))
        
        self.entity_map = model_data['entity_map']
        self.relation_map = model_data['relation_map']
        self.embedding_dim = model_data['embedding_dim']
        self.hidden_dim = model_data['hidden_dim']
        self.num_bases = model_data['num_bases']
        
        self.model = RGCNModel(
            in_feat=self.embedding_dim,
            hidden_feat=self.hidden_dim,
            out_feat=self.embedding_dim,
            num_rels=len(self.relation_map),
            num_bases=self.num_bases
        )
        
        self.model.load_state_dict(model_data['model_state'])
        self.model = self.model.to(self.device)
        print(f"Model loaded to {self.device}")
        
    def clear_cache(self):
        """
        キャッシュをクリア
        """
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            torch.mps.empty_cache()
            
        print("Cache cleared")

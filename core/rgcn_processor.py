from typing import Dict, List, Any, Optional, Tuple, Union
import json
import os
import time

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import dgl
    from dgl.nn.pytorch import RelGraphConv
    TORCH_DGL_AVAILABLE = True
except ImportError:
    print("PyTorch or DGL not available. R-GCN functionality will be limited.")
    TORCH_DGL_AVAILABLE = False
    
    try:
        import networkx as nx
        NX_AVAILABLE = True
    except ImportError:
        print("NetworkX not available. Using basic graph implementation.")
        NX_AVAILABLE = False

class RGCNProcessor:
    """
    R-GCN（Relational Graph Convolutional Network）を使用した知識グラフ処理
    """
    
    def __init__(self, device: Optional[str] = None, hidden_dim: int = 64, use_compatibility_mode: bool = False):
        """
        R-GCNプロセッサの初期化
        
        Args:
            device: 使用するデバイス（'cuda', 'mps', 'cpu'）
            hidden_dim: 隠れ層の次元数
            use_compatibility_mode: 互換モードを使用するかどうか
        """
        self.device = "cpu"
        self.hidden_dim = hidden_dim
        self.use_compatibility_mode = use_compatibility_mode
        
        if use_compatibility_mode:
            print("R-GCN running in compatibility mode (forced by user)")
            return
        
        if TORCH_DGL_AVAILABLE:
            if device is None:
                if torch.cuda.is_available():
                    self.device = "cuda"
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    self.device = "mps"
            else:
                self.device = device
                
            print(f"R-GCN using device: {self.device}")
        else:
            print("R-GCN running in compatibility mode (PyTorch/DGL not available)")
        
        self.entity_map = {}  # エンティティ名からIDへのマッピング
        self.relation_map = {}  # 関係名からIDへのマッピング
        self.id_to_entity = {}  # IDからエンティティ名へのマッピング
        self.id_to_relation = {}  # IDから関係名へのマッピング
        
        self.model = None
        self.optimizer = None
        
        self.graph = None
        self.nx_graph = None
    
    def build_graph(self, triples: List[Tuple[str, str, str]]):
        """
        トリプルからグラフを構築
        
        Args:
            triples: (主語, 関係, 目的語)のタプルのリスト
            
        Returns:
            構築されたグラフ
        """
        if TORCH_DGL_AVAILABLE:
            return self._build_dgl_graph(triples)
        elif NX_AVAILABLE:
            return self._build_networkx_graph(triples)
        else:
            return self._build_basic_graph(triples)
    
    def _build_dgl_graph(self, triples: List[Tuple[str, str, str]]):
        """DGLグラフを構築"""
        for s, r, o in triples:
            if s not in self.entity_map:
                self.entity_map[s] = len(self.entity_map)
                self.id_to_entity[len(self.entity_map) - 1] = s
            if o not in self.entity_map:
                self.entity_map[o] = len(self.entity_map)
                self.id_to_entity[len(self.entity_map) - 1] = o
            if r not in self.relation_map:
                self.relation_map[r] = len(self.relation_map)
                self.id_to_relation[len(self.relation_map) - 1] = r
        
        src = []
        dst = []
        rel = []
        
        for s, r, o in triples:
            src.append(self.entity_map[s])
            dst.append(self.entity_map[o])
            rel.append(self.relation_map[r])
        
        g = dgl.graph((src, dst))
        g.edata['rel'] = torch.tensor(rel)
        
        g.ndata['h'] = torch.randn(g.num_nodes(), self.hidden_dim)
        
        self._init_model(g.num_nodes(), len(self.relation_map))
        
        self.graph = g
        return g
    
    def _build_networkx_graph(self, triples: List[Tuple[str, str, str]]):
        """NetworkXグラフを構築"""
        G = nx.DiGraph()
        
        for s, r, o in triples:
            G.add_edge(s, o, relation=r)
            
            if s not in self.entity_map:
                self.entity_map[s] = len(self.entity_map)
                self.id_to_entity[len(self.entity_map) - 1] = s
            if o not in self.entity_map:
                self.entity_map[o] = len(self.entity_map)
                self.id_to_entity[len(self.entity_map) - 1] = o
            if r not in self.relation_map:
                self.relation_map[r] = len(self.relation_map)
                self.id_to_relation[len(self.relation_map) - 1] = r
        
        self.nx_graph = G
        return G
    
    def _build_basic_graph(self, triples: List[Tuple[str, str, str]]):
        """基本的なグラフ構造を構築"""
        graph = {
            "nodes": set(),
            "edges": []
        }
        
        for s, r, o in triples:
            graph["nodes"].add(s)
            graph["nodes"].add(o)
            graph["edges"].append((s, r, o))
            
            if s not in self.entity_map:
                self.entity_map[s] = len(self.entity_map)
                self.id_to_entity[len(self.entity_map) - 1] = s
            if o not in self.entity_map:
                self.entity_map[o] = len(self.entity_map)
                self.id_to_entity[len(self.entity_map) - 1] = o
            if r not in self.relation_map:
                self.relation_map[r] = len(self.relation_map)
                self.id_to_relation[len(self.relation_map) - 1] = r
        
        return graph
    
    def _init_model(self, num_nodes: int, num_rels: int):
        """R-GCNモデルを初期化"""
        if not TORCH_DGL_AVAILABLE:
            return
            
        class RGCN(nn.Module):
            def __init__(self, in_dim, h_dim, num_rels):
                super(RGCN, self).__init__()
                self.conv1 = RelGraphConv(in_dim, h_dim, num_rels, regularizer='basis', num_bases=4)
                self.conv2 = RelGraphConv(h_dim, h_dim, num_rels, regularizer='basis', num_bases=4)
                
            def forward(self, g, h, r):
                h = self.conv1(g, h, r)
                h = F.relu(h)
                h = self.conv2(g, h, r)
                return h
        
        self.model = RGCN(self.hidden_dim, self.hidden_dim, num_rels)
        self.model.to(self.device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)
    
    def train(self, graph, num_epochs: int = 50):
        """
        R-GCNモデルを訓練
        
        Args:
            graph: 訓練に使用するグラフ
            num_epochs: エポック数
        """
        if not TORCH_DGL_AVAILABLE or self.model is None:
            print("PyTorch/DGL not available or model not initialized. Skipping training.")
            return
            
        graph = graph.to(self.device)
        features = graph.ndata['h'].to(self.device)
        edge_type = graph.edata['rel'].to(self.device)
        
        for epoch in range(num_epochs):
            self.model.train()
            self.optimizer.zero_grad()
            
            logits = self.model(graph, features, edge_type)
            
            loss = torch.norm(logits)
            
            loss.backward()
            self.optimizer.step()
            
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{num_epochs}, Loss: {loss.item():.4f}")
    
    def get_entity_embedding(self, entity: str):
        """
        エンティティの埋め込みを取得
        
        Args:
            entity: エンティティ名
            
        Returns:
            エンティティの埋め込みベクトル
        """
        if not TORCH_DGL_AVAILABLE or self.model is None or self.graph is None:
            return None
            
        if entity not in self.entity_map:
            return None
            
        entity_id = self.entity_map[entity]
        
        self.model.eval()
        with torch.no_grad():
            graph = self.graph.to(self.device)
            features = graph.ndata['h'].to(self.device)
            edge_type = graph.edata['rel'].to(self.device)
            
            embeddings = self.model(graph, features, edge_type)
            entity_embedding = embeddings[entity_id].cpu().numpy()
            
            return entity_embedding
    
    def find_related_entities(self, entity: str, top_k: int = 5):
        """
        関連エンティティを検索
        
        Args:
            entity: 検索対象のエンティティ
            top_k: 返す関連エンティティの数
            
        Returns:
            関連エンティティのリスト
        """
        if TORCH_DGL_AVAILABLE and self.model is not None and self.graph is not None:
            return self._find_related_entities_dgl(entity, top_k)
        elif NX_AVAILABLE and self.nx_graph is not None:
            return self._find_related_entities_networkx(entity, top_k)
        else:
            return self._find_related_entities_basic(entity, top_k)
    
    def _find_related_entities_dgl(self, entity: str, top_k: int = 5):
        """DGLを使用して関連エンティティを検索"""
        if entity not in self.entity_map:
            return []
            
        entity_id = self.entity_map[entity]
        
        self.model.eval()
        with torch.no_grad():
            graph = self.graph.to(self.device)
            features = graph.ndata['h'].to(self.device)
            edge_type = graph.edata['rel'].to(self.device)
            
            embeddings = self.model(graph, features, edge_type)
            entity_embedding = embeddings[entity_id]
            
            similarities = F.cosine_similarity(entity_embedding.unsqueeze(0), embeddings)
            
            similarities[entity_id] = -1.0
            
            top_indices = torch.topk(similarities, top_k).indices.cpu().numpy()
            
            related_entities = []
            for idx in top_indices:
                related_entities.append({
                    "entity": self.id_to_entity[idx],
                    "similarity": similarities[idx].item()
                })
            
            return related_entities
    
    def _find_related_entities_networkx(self, entity: str, top_k: int = 5):
        """NetworkXを使用して関連エンティティを検索"""
        if entity not in self.nx_graph:
            return []
            
        neighbors = list(self.nx_graph.successors(entity)) + list(self.nx_graph.predecessors(entity))
        neighbors = list(set(neighbors))  # 重複を削除
        
        related_entities = []
        for neighbor in neighbors[:top_k]:
            related_entities.append({
                "entity": neighbor,
                "similarity": 1.0  # NetworkXでは類似度を計算しないので1.0とする
            })
            
        return related_entities
    
    def _find_related_entities_basic(self, entity: str, top_k: int = 5):
        """基本的なグラフ構造を使用して関連エンティティを検索"""
        if not hasattr(self, 'graph') or self.graph is None:
            return []
            
        related = []
        
        for s, r, o in self.graph["edges"]:
            if s == entity and o not in related:
                related.append(o)
            elif o == entity and s not in related:
                related.append(s)
                
        return [{"entity": e, "similarity": 1.0} for e in related[:top_k]]
    
    def save_graph(self, path: str):
        """
        グラフを保存
        
        Args:
            path: 保存先のパス
        """
        data = {
            "entity_map": self.entity_map,
            "relation_map": self.relation_map,
            "id_to_entity": self.id_to_entity,
            "id_to_relation": self.id_to_relation
        }
        
        if TORCH_DGL_AVAILABLE and self.graph is not None:
            src, dst = self.graph.edges()
            edge_type = self.graph.edata['rel']
            
            data["edges"] = {
                "src": src.tolist(),
                "dst": dst.tolist(),
                "type": edge_type.tolist()
            }
        elif NX_AVAILABLE and self.nx_graph is not None:
            edges = []
            for s, o, attrs in self.nx_graph.edges(data=True):
                edges.append({
                    "src": s,
                    "dst": o,
                    "rel": attrs.get("relation", "")
                })
            data["nx_edges"] = edges
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_graph(self, path: str):
        """
        グラフを読み込み
        
        Args:
            path: 読み込み元のパス
            
        Returns:
            読み込まれたグラフ
        """
        if not os.path.exists(path):
            print(f"グラフファイルが見つかりません: {path}")
            return None
            
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.entity_map = data.get("entity_map", {})
        self.relation_map = data.get("relation_map", {})
        self.id_to_entity = data.get("id_to_entity", {})
        self.id_to_relation = data.get("id_to_relation", {})
        
        self.id_to_entity = {int(k): v for k, v in self.id_to_entity.items()}
        self.id_to_relation = {int(k): v for k, v in self.id_to_relation.items()}
        
        if TORCH_DGL_AVAILABLE and "edges" in data:
            edges = data["edges"]
            src = torch.tensor(edges["src"])
            dst = torch.tensor(edges["dst"])
            edge_type = torch.tensor(edges["type"])
            
            g = dgl.graph((src, dst))
            g.edata['rel'] = edge_type
            
            g.ndata['h'] = torch.randn(g.num_nodes(), self.hidden_dim)
            
            self._init_model(g.num_nodes(), len(self.relation_map))
            
            self.graph = g
            return g
        elif NX_AVAILABLE and "nx_edges" in data:
            G = nx.DiGraph()
            
            for edge in data["nx_edges"]:
                G.add_edge(edge["src"], edge["dst"], relation=edge["rel"])
                
            self.nx_graph = G
            return G
            
        return None

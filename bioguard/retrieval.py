"""Local dense, lexical and boundary-paired retrieval."""
from collections import Counter
import math
import re
from . import core as guard


class BoundaryRetriever(guard.Retriever):
    def rank(self,question,method,top_k=3):
        if method!='hybrid':return super().rank(question,method,top_k)
        ranked=super().rank(question,method,12)
        # Keep two query-relevant hits, then add a paired boundary explanation.
        selected=ranked[:2];ids={r['id'] for r in selected}
        pairs={'KB06':'KB41','KB18':'KB41','KB11':'KB41','KB19':'KB41',
               'KB04':'KB42','KB09':'KB42','KB29':'KB42','KB30':'KB42',
               'KB07':'KB43','KB20':'KB43','KB23':'KB43','KB31':'KB43','KB32':'KB43'}
        counterpart=next((pairs[r['id']] for r in ranked[:3] if r['id'] in pairs and pairs[r['id']] not in ids),None)
        if counterpart:selected.append(dict(id=counterpart,score=None,selection='boundary_pair'))
        else:selected.append(next(r for r in ranked if r['id'] not in ids))
        return selected


def tokens(text):
    out=[]
    for p in re.findall(r'[\u3400-\u9fff]+|[a-z0-9]+',text.lower()):
        out.extend([p[i:i+2] for i in range(len(p)-1)] if '\u3400'<=p[0]<='\u9fff' else [p])
    return out


class EvidenceRetriever(BoundaryRetriever):
    def __init__(self,cards):
        super().__init__(cards)
        self.freqs=[Counter(tokens(t)) for t in self.expanded_texts]
        self.lengths=[sum(t.values()) for t in self.freqs]
        self.avg_len=sum(self.lengths)/len(self.lengths)
        df=Counter(t for f in self.freqs for t in f)
        self.bm_idf={t:math.log(1+(len(cards)-n+.5)/(n+.5)) for t,n in df.items()}

    def rank(self,question,method,top_k=3):
        if method in ('none','dense','hybrid','full'):
            return super().rank(question,method,top_k)
        if method=='boundary':return super().rank(question,'hybrid',top_k)
        if method=='low_relevance':
            rows=super().rank(question,'dense',len(self.cards))[-top_k:]
            return [dict(**r,selection='lowest_dense_control') for r in rows]
        if method!='fusion':raise ValueError('Unknown retrieval method')
        q=self.encode(['为这个句子生成表示以用于检索相关文章：'+question])[0]
        dense=(self.vectors@q).tolist()
        expanded=(self.expanded_vectors@q).tolist()
        terms=set(tokens(question));bm=[]
        for freqs,length in zip(self.freqs,self.lengths):
            bm.append(sum(self.bm_idf.get(t,0)*freqs[t]*2.5/(freqs[t]+1.5*(.25+.75*length/self.avg_len)) for t in terms if freqs[t]))
        orders=[sorted(range(len(self.cards)),key=lambda i:(-scores[i],self.cards[i]['id'])) for scores in (dense,expanded,bm)]
        ranks=[{i:r+1 for r,i in enumerate(order)} for order in orders]
        fused=[sum(1/(60+r[i]) for r in ranks) for i in range(len(self.cards))]
        order=sorted(range(len(self.cards)),key=lambda i:(-fused[i],self.cards[i]['id']))
        return [dict(id=self.cards[i]['id'],score=round(fused[i],8),score_type='rrf_k60',
            component_ranks=dict(zip(('dense','expanded','bm25'),[r[i] for r in ranks]))) for i in order[:top_k]]

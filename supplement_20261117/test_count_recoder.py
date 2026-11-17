from collections import Counter
import h3
from datasets import sample
from methods_count import CountRecoder
from methods_v2 import LocalRecoder

def test():
    assert CountRecoder(8).count([],[],[])==Counter()
    try:CountRecoder(8).count([30.2],[],[])
    except ValueError:pass
    else:raise AssertionError('length mismatch must reject')
    for rf,rc in [(9,8),(10,8),(10,9)]:
        for distribution in ['U','C','B']:
            lat,lon=sample('hangzhou',distribution,1000,42,rc)
            fine=[h3.latlng_to_cell(a,b,rf) for a,b in zip(lat,lon)]
            expected=Counter(h3.latlng_to_cell(a,b,rc) for a,b in zip(lat,lon))
            obj=CountRecoder(rc)
            assert obj.count(lat,lon,fine)==expected
            assert obj.count(lat,lon,fine)==expected # warm cache, unchanged output
            assert obj.count(lat+lat,lon+lon,fine+fine)==Counter({k:2*v for k,v in expected.items()})
            m2=LocalRecoder(rc).assign(lat,lon,fine)[0]
            assert Counter(m2)==expected
    print('PASS: empty input, input validation, duplicate multiplicity, warm reuse and 9 direct-oracle cases')
if __name__=='__main__':test()

#AUTOGENERATED! DO NOT EDIT! File to edit: dev/pspace.ipynb (unless otherwise specified).

__all__ = ['Axis', 'ParameterSpace']

#Cell
import numpy as np

class Axis():
    def __init__(self, name, values):
        self.name = name
        self.values = values

    def __iter__(self):
        return iter((self.name,self.values))



#Cell
from collections import OrderedDict


class ParameterSpace():
    def __init__(self, axes, _locals={}):
        self._locals = _locals
        self._axes = OrderedDict()
        self._keys = []
        self._init = {}
        self.shape = ()

        if isinstance(axes, dict):
            axes = axes.items()

        for axis in axes:
                key, vals = axis
                self._add_axis(key, vals)

        assert len(self) >= 0


    def sample(self, key=None):
        if key is None:
            t = np.random.choice(len(self))
            x = self[t]
        else:
            x = np.random.choice(self._axes[key])

        return x

    def add(self, key, init, vals):
            print(f"...{key}={init}; {vals}")
            self._axes[key] = vals
            self._keys.append(key)
            self.shape += (len(vals),)
            self._init[key] = init
            exec(f"{key}={init};", None, self._locals)

    def _add_axis(self, key, vals):
            self._axes[key] = vals
            self._keys.append(key)
            self.shape += (len(vals),)
            self._init[key] = vals[0]

    def reset(self, t):
        c = self[t]
        print("Resetting:")
        for k,v in c.items():
            print(f"...{k}={v}")
            exec(f"{k}={v};", None, self._locals)

    @staticmethod
    def _get_multi_index(t, shape):
        n = len(shape)
        I = [None]*n
        for k in range(0,n):
            i = t//np.prod(shape[k+1:])
            I[k] = int(i)%shape[k]

        return I


    def __getitem__(self, i):
        if i == -1: return self._init
        I = self._get_multi_index(i,self.shape)
        c = {}
        for k,i in enumerate(I):
            key = self._keys[k]
            c[key] = self._axes[key][i]

        return c

    def __call__(self, key, init, vals):
        return self.add(key, init, vals)


    def _coords(self, c):
        I = [None]*len(self.shape)
        assert isinstance(c, dict)


        for k,v in c.items():
            j = self._keys.index(k)
            I[j] = list(self._axes[k]).index(v)

        return I

    def find(self, c):
        assert isinstance(c, dict)
        I = self._coords(c)

        t = 0
        for j,i in enumerate(I):
            t += i*np.prod(self.shape[j+1:])

        return int(t)

    def slice(self, **fixed):
        fixed = dict([(k,v) for k,v in fixed.items() if v is not None])

        keys  = self._keys

        free = []
        for i,k in enumerate(keys):
            if k not in fixed.keys():
                free.append(i)




        sl_shape = tuple([self.shape[i] for i in free])

        Z = np.indices(sl_shape)		
        X = np.zeros((self.dim,*sl_shape))

        x = self._coords(fixed)

        count = 0
        for i in range(self.dim):
            if x[i] is None:
                X[i] = Z[count]
                count+=1
            else:
                X[i] = x[i]

        fac = np.array([np.prod(self.shape[j+1:]) for j in range(self.dim)])
        fac = fac.reshape((-1,)+(1,)*len(free))

        print(f"Slice:")
        print(" - "+ ", ".join([f"{k}={v}" for k,v in fixed.items()]))
        print(" - "+ ", ".join([f"{keys[i]}={self._axes[keys[i]]}" for i in free]))


        return np.sum(fac*X, axis=0).astype(int)



    @property
    def dim(self):
        return len(self.shape)

    def __len__(self):
        if len(self.shape)>0: return np.product(self.shape)
        else: return 0

    def __str__(self):
        s = "ParameterSpace(\n"
        for key, axis in self._axes.items():
            s += f"\t{key}:\t{axis}\n"
        s += ")"
        return s


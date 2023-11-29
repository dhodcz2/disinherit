## Disinherit

This solution involves copying (and caching) the MRO of the class,
removing the attributes from each of the copies, and then reassembling the class.

```
from disinherit import disinherit
from pandas import DataFrame
dataframe = disinherit(DataFrame, '__getattr__')
assert dataframe is not DataFrame
assert dataframe.__new__ is DataFrame.__new__
assert dataframe.__init__ is DataFrame.__init__
assert not hasattr(dataframe, '__getattr__')
```

## Why would you do this?!

I was having problems with `pandas.DataFrame.__getattr__`, specifically that it exists at all,
and could not find a better workaround. Overriding is not an option.
In the rare case that someone else has the same problem,
I decided to make this solution available. In exchange please smack that star button.

## Are you sure?

```python
from pandas import DataFrame

class Test(DataFrame):
    @property
    def foo(self):
        print('foo')
        raise AttributeError

test = Test()
test.foo
```

```
foo
foo
Traceback (most recent call last):
  ...
AttributeError
```

Here you can see that foo is printed twice. This is troublesome for the library that I am working on.

```python
from pandas import DataFrame
from disinherit import disinherit
NoGetter = disinherit(DataFrame, '__getattr__')
class Test(NoGetter):
    @property
    def foo(self):
        print('foo')
        raise AttributeError

test = Test()
test.foo
```
```
foo
Traceback (most recent call last):
    ...
AttributeError
```
Now because `__getattr__` is not inherited, there is no problematic recursive behavior.


## Installation

I'm not allowed in the PyPI clubhouse yet, so you'll have to install from source:

```
git clone git@github.com:dhodcz2/disinherit.git
python -m pip install ./disinherit
```


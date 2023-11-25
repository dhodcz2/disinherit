## Removing Inherited Attributes

This solution involves copying (and cacheing) tHe MRO of the class,
removing the attributes from each of the copies, and then reassembling the class.

```
from remove_inherited_attributes import remove_inherited_attributes
from pandas import DataFrame
dataframe = remove_inherited_attributes(DataFrame, '__getattr__')
assert dataframe is not DataFrame
assert not hasattr(dataframe, '__getattr__')
```

## Why would you do this?!

I was having problems with pandas.DataFrame.__getattr__, specifically that it exists at all,
and could not find a better workaround. Overriding is not an option.
In the rare case that someone else has the same problem,
I decided to make this solution available. In exchange please smack that star button.

## Installation

I'm not allowed in the PyPI clubhouse yet, so you'll have to install from source:

```
git clone git@github.com:dhodcz2/remove_inherited_attributes.git
```


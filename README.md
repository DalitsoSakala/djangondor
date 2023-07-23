# djangondor

[![PyPI - Version](https://img.shields.io/pypi/v/djangondor.svg)](https://pypi.org/project/djangondor)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/djangondor.svg)](https://pypi.org/project/djangondor)

-----

**Table of Contents**

- [Installation](#installation)
- [Template tags](#templatetags)
- [Helper functions](#functions)
- [License](#license)

## Installation

```console
pip install djangondor
```

## Functions

### Collections package

#### dict_values

> dict_values can be used to access data in a dict as a tuple

```python

from djangondor.collections import dict_values

data = {'name':'Joseph','age':30,'height':1.7}
name, height = dict_values(data,'name','height')

```

#### value_list

> Complements the builtin `Queryset.values_list` returning one data item per entry in the list. However, it only allows you to retrieve one field per item in the queryset.

```python
from djangondor.collections import value_list

queryset = User.objects.all()

# data would have => ['sam', 'musonda', 'waza', 'chilu']
data = value_list(queryset, 'first_name')



```

## Templatetags

### Path tags

```html
{% load djangondor_path_tags%}

<a href="{% url 'index:index'  %}" class="{% active_app 'index'%}">Index App</a>



<a href="{% url 'index:home'  %}" class="{% active_path 'home'%}">Home</a>
<a href="{% url 'index:about'  %}" class="{% active_path 'about'%}">About</a>

<a href="{% url 'index:settings'  %}" class="{% active_path_in 'home_settings' 'profile_settings' %}">Settings</a>

<!-- Would produce the following if navigation matched 'index:home': -->

<a href="/" class="active">Index App</a>



<a href="/" class="active">Home</a>
<a href="/about" class="">About</a>

<a href="/settings" class="">Settings</a>
```

## License

`djangondor` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

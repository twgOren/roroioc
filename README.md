[![Build Status](https://travis-ci.org/twgOren/roroioc.svg?branch=master)](https://travis-ci.org/twgOren/roroioc)

# RORO IOC

As in [roll on roll off](https://en.wikipedia.org/wiki/Roll-on/roll-off),
is a dependency injection framework. It is contextual and high performance.

# Example

```python
from attr import attrs, attrib
from roro_ioc import INJECTED, create_ioc_container, inject


@attrs
class ApplicationContext(object):
    my_data_set = attrib()


APP_CONTEXT_IOC_CONTAINER = create_ioc_container(ApplicationContext)


@inject(APP_CONTEXT_IOC_CONTAINER)
def get_data(my_data_set=INJECTED):
    print('Copying data from {}'.format(my_data_set))


my_context = ApplicationContext(my_data_set='s3://bucket/data')

with APP_CONTEXT_IOC_CONTAINER.arm(my_context):
    get_data()  # prints: "Copying data from s3://bucket/data"
```

# License

Copyright (c) 2018 Twiggle Ltd.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


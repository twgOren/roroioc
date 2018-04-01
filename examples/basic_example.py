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

======
GenAPI
======

GenAPI is a Python API for the Genesis platform.

=======
Install
=======

To install, run::

  python setup.py install

To install for development, run::

  python setup.py develop

=====
Usage
=====

Create an API instance:

.. code-block:: python

   gen = GenCloud('anonymous', 'anonymous', 'http://cloud.genialis.com')


Get all project and select the first one:

.. code-block:: python

   projects = gen.projects()
   project = projects.itervalues().next()

Get expression objects and select the first one:

.. code-block:: python

   objects = project.objects(type__startswith='data:expression')
   object = object.itervalues().next()

Print annotation:

.. code-block:: python

   object.print_annotation()

Print file fields:

.. code-block:: python

   object.print_downloads()

Download file:

.. code-block:: python

   object.download('output.rpkum')

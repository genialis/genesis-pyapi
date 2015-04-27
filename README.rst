=============
Genesis PyAPI
=============

Python API for the Genesis platform.


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

   from genesis import Genesis
   gen = Genesis()


Get all project and select the first one:

.. code-block:: python

   projects = gen.projects()
   project = list(projects.values())[0]

Get expression objects and select the first one:

.. code-block:: python

   expressions = project.data(type__startswith='data:expression:')
   expression = expressions[0]

Print annotation:

.. code-block:: python

   expression.print_annotation()

Print file fields:

.. code-block:: python

   expression.print_downloads()

Download file:

.. code-block:: python

   filename = expression.annotation['output.exp']['value']['file']
   resp = expression.download('output.exp')
   with open(filename, 'w') as fd:
       fd.write(resp.content)

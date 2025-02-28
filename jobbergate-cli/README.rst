================
 Jobbergate CLI
================

The Jobbergate CLI provides a command-line interface to view and manage the Jobbergate
resources. It can be used to create Job Scripts from template and then submit them to
the Slurm cluster to which Jobbergate is connected.

Jobbergate CLI is a Python project implemented with the
`Typer <https://typer.tiangolo.com/>`_ CLI builder library. Its dependencies and
environment are managed by `Poetry <https://python-poetry.org/>`_.

The CLI has a rich help system that can be accessed by passing the ``--help`` flag to
the main command:

.. code-block:: console

   jobbergate job-scripts --help


There is also help and parameter guides for each of the subcommands that can be accessed
by passing them the ``--help`` flag:

.. code-block:: console

   jobbergate job-scripts list --help

See also:

* `jobbergate-api <https://github.com/omnivector-solutions/jobbergate/jobbergate-api>`_

License
-------
* `MIT <LICENSE>`_


Copyright
---------
* Copyright (c) 2020 OmniVector Solutions <info@omnivector.solutions>

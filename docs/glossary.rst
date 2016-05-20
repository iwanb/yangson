.. _glossary:

========
Glossary
========

.. glossary::
   :sorted:

   raw value

      A value of an instance that is produced by the Python parser
      from serialised JSON data. Based on its type and data model
      information, a raw value is transformed to a :term:`cooked
      value`.

   cooked value

      An instance value that is in the internal form prescribed for
      that instance. That is, scalar values are represented according
      to their types, while objects and arrays are instances of a
      subclass of :class:`Instance`.

   qualified name

       A tuple in the form *(name, module)* where *name* is the name
       of a YANG entity (schema node, feature, identity etc.), and
       *module* is the name of the YANG module in which the entity is
       defined. Python type alias for the qualified name is
       :const:`QualName`.

   schema route

       A list of :term:`qualified name`\ s of schema nodes interpreted
       relative to a given reference schema node and uniquely
       identifies its descendant schema node. Python type alias for
       the schema route is :const:`SchemaRoute`.

   data route

       A list of :term:`qualified name`\ s of data nodes interpreted
       relative to a given reference schema node. As a :term:`schema
       route`, a data route also identifes a unique descendant schema
       node because names of data nodes belonging to the cases of the
       same choice are required to be unique, see sec. `6.2.1`_ in
       [Bjo16]_.

   prefixed name

       A string in the form [*prefix*\ :]\ *name* where *name* is the
       name of a YANG entity (schema node, feature, identity etc.),
       and *prefix* is the namespace prefix declared for the module in
       which the entity is defined. Python type alias for the prefixed
       name is :const:`PrefName`.

   YANG identifier

       A string satisfying the rules for a YANG identifier (see
       sec. `6.2`_ in [Bjo16]_): it starts with an uppercase or
       lowercase ASCII letter or an underscore character (``_``),
       followed by zero or more ASCII letters, digits, underscore
       characters, hyphens, and dots. Python type alias for the YANG
       identifier is :const:`YangIdentifier`.

   module identifier

       A tuple in the form *(module_name, revision)* that identifies a
       particular revision of a module. The second component,
       *revision*, is either a revision date (string in the form
       ``YYYY-MM-DD``) or ``None``. In the latter case the revision is
       unspecified.

   schema path

       A string of slash-separated schema node names in the form
       [*module_name*\ ``:``]\ *schema_node_name*. The initial
       component must always be qualified with a module name. Any
       subsequent component is qualified with a module name if and
       only if its namespace is different from the previous
       component. A schema path is always absolute, i.e. starts at the
       top of the schema. A leading slash is optional. Python type
       alias for the schema path is :const:`SchemaPath`.

   data path

       A special form of :term:`schema path` containing only names of
       *data nodes*. The relationship of data path and schema path is
       analogical to how :term:`data route` is related to
       :term:`schema route`.

   schema node identifier

       A sequence of :term:`prefixed name`\ s of schema nodes
       separated with slashes. A schema node identifier that starts
       with a slash is absolute, otherwise it is relative. See
       [Bjo16]_, sec. `6.5`_.

   instance name

       A string in the form [*module_name*\ ``:``]\ *name* where
       *name* is a name of a data node. Instance names identify nodes
       in the data tree, and are used both as :class:`ObjectValue`
       keys and member names in JSON serialization. See [Lho16]_,
       sec. `4`_ for details. Python type alias for the instance name
       is :const:`InstanceName`.

   instance route

       A list of :term:`instance name`\ s that specifies a route
       between a context node in the instance data tree and its
       descendant node. Python type alias for the instance route is
       :const:`InstanceRoute`.

   instance identifier

       A string that identifies a unique instance in the data
       tree. The syntax of instance identifiers is defined in
       [Bjo16]_, sec. `9.13`_, and [Lho16]_, sec. `6.11`_.

   resource identifier

       A string identifying an instance in the data tree that is
       suitable for use in URLs. The syntax of resource identifiers is
       defined in [BBW16a]_, sec. `3.5.1`.

   implemented module

       A YANG module that contributes data nodes to the data model. In
       YANG library, implemented modules have the *conformance-type*
       parameter set to ``implement``. See [BBW16]_, sec. `2.2`_.

   imported-only module

       A YANG module whose data nodes aren't contributed to the data
       model. Other modules import such a module in order to use its
       typedefs and/or groupings. In YANG library, implemented modules
       have the *conformance-type* parameter set to ``import``. See
       [BBW16]_, sec. `2.2`_.

   namespace identifier

       A string identifying the namespace of names defined in a YANG
       module or submodule. For main modules, the namespace identifier
       is identical to the module name whereas for submodules it is
       the name of the main module to which the submodule belongs.

.. _2.2: https://tools.ietf.org/html/draft-ietf-netconf-yang-library#section-2.2
.. _3.5.1: https://tools.ietf.org/html/draft-ietf-netconf-restconf#section-3.5.1
.. _4: https://tools.ietf.org/html/draft-ietf-netmod-yang-json#section-4
.. _6.2: https://tools.ietf.org/html/draft-ietf-netmod-rfc6020bis#section-6.2
.. _6.2.1: https://tools.ietf.org/html/draft-ietf-netmod-rfc6020bis#section-6.2.1
.. _6.11: https://tools.ietf.org/html/draft-ietf-netmod-yang-json#section-6.11
.. _6.5: https://tools.ietf.org/html/draft-ietf-netmod-rfc6020bis#section-6.5
.. _9.13: https://tools.ietf.org/html/draft-ietf-netmod-rfc6020bis#section-9.13
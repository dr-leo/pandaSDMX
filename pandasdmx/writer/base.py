from functools import singledispatch


class BaseWriter:
    """Base class for recursive writers.

    Usage:

    - Create an instance of this class.
    - Use :meth:`register` in the same manner as Python's built-in
      :func:`functools.singledispatch` to decorate functions that certain types
      of :mod:`sdmx.model` or :mod:`sdmx.message` objects.
    - Call :meth:`recurse` to kick off recursive writing of objects, including
      from inside other functions.

    Example
    -------
    MyWriter = BaseWriter('my')

    @MyWriter.register
    def _(obj: sdmx.model.ItemScheme):
        ... code to write an ItemScheme ...
        return result

    @MyWriter.register
    def _(obj: sdmx.model.Codelist):
        ... code to write a Codelist ...
        return result
    """

    def __init__(self, format_name):
        # Create the single-dispatch function
        @singledispatch
        def func(obj, *args, **kwargs):
            raise NotImplementedError(
                f"write {obj.__class__.__name__} to " f"{format_name}"
            )

        self._dispatcher = func

    def recurse(self, obj, *args, **kwargs):
        """Recursively write *obj*.

        If there is no :meth:`register` 'ed function to write the class of
        `obj`, then the parent class of `obj` is used to find a method.
        """
        # TODO use a cache to speed up the MRO does not need to be traversed
        #      for every object instance

        dispatcher = getattr(self, "_dispatcher")
        try:
            # Let the single dispatch function choose the overload
            return dispatcher(obj, *args, **kwargs)
        except NotImplementedError as exc:
            try:
                # Use the object's parent class to get a different overload
                func = dispatcher.registry[obj.__class__.mro()[1]]
            except KeyError:
                # Overload for the parent class did not exist
                raise exc

            return func(obj, *args, **kwargs)

    def __call__(self, func):
        """Register *func* as a writer for a particular object type."""
        dispatcher = getattr(self, "_dispatcher")
        dispatcher.register(func)
        return func

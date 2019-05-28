# pandaSDMX is licensed under the Apache 2.0 license a copy of which
# is included in the source distribution of pandaSDMX.
# This is notwithstanding any licenses of third-party software included in this distribution.
# (c) 2014-2018 Dr. Leo <fhaxbox66qgmail.com>

'''


This module is part of the pandaSDMX package

        SDMX 2.1 information model

(c) 2014 Dr. Leo (fhaxbox66@gmail.com)
'''

from pandasdmx.utils import DictLike, concat_namedtuples, str2bool
from operator import attrgetter, or_
from collections import defaultdict
from functools import reduce


class SDMXObject(object):

    def __init__(self, reader, elem, **kwargs):

        object.__setattr__(self, '_reader', reader)
        object.__setattr__(self, '_elem', elem)
        super(SDMXObject, self).__init__(**kwargs)


class Header(SDMXObject):

    def __init__(self, *args, **kwargs):
        super(Header, self).__init__(*args, **kwargs)
        # Set additional attributes present in DataSet messages
        for name in ['structured_by', 'dim_at_obs']:
            value = getattr(self._reader, name)(self)
            if value:
                setattr(self, name, value)

    @property
    def id(self):
        return self._reader.read_as_str('headerID', self)

    @property
    def prepared(self):
        return self._reader.read_as_str('header_prepared', self)

    @property
    def sender(self):
        return self._reader.read_as_str('header_sender', self)

    @property
    def receiver(self):
        return self._reader.read_as_str('header_receiver', self)

    @property
    def error(self):
        return self._reader.read_as_str('error', self)


class Footer(SDMXObject):

    @property
    def text(self):
        return self._reader.read_as_str('footer_text', self, first_only=False)

    @property
    def severity(self):
        return self._reader.read_as_str('footer_severity', self)

    @property
    def code(self):
        return int(self._reader.read_as_str('footer_code', self))


class Constrainable:

    @property
    def constrained_by(self):
        if not hasattr(self, '_constrained_by'):
            if hasattr(self._reader.message, 'constraint'):
                self._constrained_by = [c for c in self._reader.message.constraint.values()
                                        if c.constraint_attachment() is self]
            else:
                self._constrained_by = []
        return self._constrained_by

    def apply(self, dim_codes=None, attr_codes=None):
        '''
        Compute the constrained code lists as frozensets by
        merging the constraints resulting from all ContentConstraint instances 
        into a dict of sets of valid codes 
        for dimensions and attributes respectively.
        Each codelist is constrained by at most one Constraint
        so that no set operations are required.

        Return tuple of constrained_dimensions(dict), constrained_attribute_codes(dict)
        '''
        dimension, attribute = {}, {}
        for c in self.constrained_by:
            d, a = c.apply(dim_codes, attr_codes)
            if d:
                dimension.update(d)
            if a:
                attribute.update(a)
        # Fill any empty slots with passed codesets. This implements
        # the inheritance mechanism.
        if dim_codes:
            for k, v in dim_codes.items():
                dimension.setdefault(k, v)
        if attr_codes:
            for k, v in attr_codes.items():
                attribute.setdefault(k, v)
        return dimension, attribute


class Annotation(SDMXObject):

    @property
    def id(self):
        return self._reader.id(self)

    @property
    def title(self):
        return self._reader.title(self)

    @property
    def annotationtype(self):
        return self._reader.read_as_str('annotationtype', self)

    @property
    def url(self):
        return self._reader.read_as_str('url', self)

    @property
    def text(self):
        return self._reader.international_str('AnnotationText', self)

    def __str__(self):
        return 'Annotation: title=%s' % self.title


class AnnotableArtefact(SDMXObject):

    @property
    def annotations(self):
        return self._reader.read_instance(Annotation, self, first_only=False)


class IdentifiableArtefact(AnnotableArtefact):

    def __init__(self, *args, **kwargs):
        super(IdentifiableArtefact, self).__init__(*args, **kwargs)
        ref = self._reader.read_instance(Ref, self)
        self.urn = self._reader.read_as_str('urn', self)
        if ref:
            self.ref = ref
        try:
            self.id = self.ref.id
        except AttributeError:
            self.id = self._reader.read_as_str('id', self)

    def __eq__(self, value):
        return self.urn == value.urn

    def __ne__(self, value):
        return self.urn != value.urn

    def __lt__(self, value):
        return self.urn < value.urn

    def __gt__(self, value):
        return self.urn > value.urn

    def __le__(self, value):
        return self.urn <= value.urn

    def __ge__(self, value):
        return self.urn >= value.urn

    def __hash__(self):
        return hash(self.urn)

    @property
    def uri(self):
        return self._reader.read_as_str('uri', self)

    def __repr__(self):
        result = ' | '.join(
            (self.__class__.__name__, self.id))
        return result


class NameableArtefact(IdentifiableArtefact):

    @property
    def name(self):
        try:
            return object.__getattribute__(self, '_name')
        except AttributeError:
            object.__setattr__(
                self, '_name', self._reader.international_str('Name', self))
            return self._name

    @property
    def description(self):
        try:
            return self._description
        except AttributeError:
            self._description = self._reader.international_str(
                'description', self)
            return self._description

    def __str__(self):
        result = ' | '.join(
            (self.__class__.__name__, self.id))
        try:
            result += (' | ' + self.name.en)
        except AttributeError:
            pass
        return result

    # Make dicts and lists of Artefacts more readable. Use pprint or altrepr
    # instead?
    __repr__ = __str__


class VersionableArtefact(NameableArtefact):

    @property
    def version(self):
        return self._reader.read_as_str('ref_version', self)

    @property
    def valid_from(self):
        return self._reader.valid_from(self)

    @property
    def valid_to(self):
        return self._reader.valid_to(self)


class MaintainableArtefact(VersionableArtefact):

    @property
    def is_final(self):
        return str2bool(self._reader.read_as_str('isfinal', self))

    @property
    def is_external_ref(self):
        return str2bool(self._reader.read_as_str('isfinal', self))

    @property
    def structure_url(self):
        return self._reader.structure_url(self)  # fix this

    @property
    def service_url(self):
        return self._reader.service_url(self)  # fix this

    @property
    def maintainer(self):
        return self._reader.read_as_str('agencyID', self)


# Helper class for ItemScheme and ComponentList.
# This is not specifically mentioned in the SDMX info-model.
# ItemSchemes and ComponentList differ only in that ItemScheme is Nameable, whereas
# ComponentList is only identifiable. Therefore, ComponentList cannot
# inherit from ItemScheme.
class Scheme(DictLike):
    # will be passed to _reader.read_identifiables. overwrite in subclasses
    _get_items = None

    def __init__(self, *args, **kwargs):
        super(Scheme, self).__init__(*args, **kwargs)
        self._reader.read_identifiables(self._get_items, self)

    # DictLike.aslist returns a list sorted by _sort_key.
    # Alphabetical order by 'id' is the default. DimensionDescriptor overrides this
    # to sort by position.
    _sort_key = attrgetter('id')

    def aslist(self):
        return sorted(self.values(), key=self._sort_key)


class ItemScheme(MaintainableArtefact, Scheme):

    @property
    def is_partial(self):
        return self._reader.is_partial(self)


class Item(NameableArtefact):

    @property
    def children(self):
        return self._reader._item_children(self)


class StructureUsage(MaintainableArtefact):

    @property
    def structure(self):
        return self._reader.read_instance(Ref, self, offset='ref_structure')


class ComponentList(IdentifiableArtefact, Scheme):
    pass


class Representation(SDMXObject):

    def __init__(self, *args, **kwargs):
        super(Representation, self).__init__(*args)
        enum_ref = self._reader.read_instance(
            Ref, self, offset='enumeration')
        if enum_ref:
            self.text_type = self.max_length = None
            self.enum = enum_ref
        else:
            self.enum = None
            self.text_type = self._reader.read_as_str('texttype', self)
            max_length = self._reader.read_as_str('maxlength', self)
            if max_length:
                self.max_length = int(max_length)
            else:
                self.max_length = None


class Facet:
    # This is not yet working. not used so far.

    facet_type = {}  # for attributes such as isSequence, interval
    facet_value_type = ('String', 'Big Integer', 'Integer', 'Long',
                        'Short', 'Double', 'Boolean', 'URI', 'DateTime',
                        'Time', 'GregorianYear', 'GregorianMonth', 'GregorianDate',
                        'Day', 'MonthDay', 'Duration')
    itemscheme_facet = u''  # to be completed

    def __init__(self, facet_type=None, facet_value_type=u'',
                 itemscheme_facet=u'', *args, **kwargs):
        self.facet_type = facet_type
        self.facet_value_type = facet_value_type
        self.itemscheme_facet = itemscheme_facet


class Concept(Item):
    pass
    # core_repr = Instance(Representation)
    # iso_concept = Instance(IsoConceptReference


class Component(IdentifiableArtefact):

    @property
    def concept_identity(self):
        return self._reader.read_instance(Ref, self, offset='concept_identity')

    @property
    def concept(self):
        concept_id = self.concept_identity.id
        parent_id = self.concept_identity.maintainable_parent_id
        return self._reader.message.conceptscheme[parent_id][concept_id]

    @property
    def local_repr(self):
        return self._reader.read_instance(Representation, self)


class Code(Item):
    pass


class Codelist(ItemScheme):
    _get_items = Code


class ConceptScheme(ItemScheme):
    _get_items = Concept


class KeyValidatorMixin(object):
    '''
    Mix-in class with methods for key validation. Relies on properties computing 
    code sets, constrained codes etc. Subclasses are DataMessage and
    CodelistHandler which is, in turn, inherited by StructureMessage.
    '''

    def _in_codes(self, key, raise_error=True):
        '''
        key: a prepared key, i.e. multiple values within a dimension
        must be represented as list of strings.

        This method is called by self._in_constraints. Thus it does not 
        be called from application code.

args:
    key(dict): normalized key, i.e. values must be lists of str
    raises_error(bool): if True (default),
        ValueError is raised if at least one value within key
        is not in the (unconstrained) codes. Otherwise, False is returned.
        If all values from key are in the respective code list,
        True is returned

        '''
        # First, check keys against dim IDs
        invalid = [k for k in key if k not in self._dim_ids]
        if invalid:
            raise ValueError(
                'Invalid dimension ID(s) {0}, allowed are: {1}'.format(invalid, self._dim_ids))
        # Raise error if some value is not of type list
        if [k for k in key.values() if not isinstance(k, list)]:
            raise TypeError(
                'All values of the key-dict must be of type ``list``.')
        # Check values against codelists
        invalid = defaultdict(list)
        for k, values in key.items():
            for v in values:
                if v not in self._dim_codes[k]:
                    invalid[k].append(v)
        if invalid:
            if raise_error:
                raise ValueError(
                    'Value(s) not in codelists.', invalid)
            else:
                return False
        return True

    def _in_constraints(self, key, raise_error=True):
        '''
        check key against all constraints, i.e. the constrained
        code lists.

        args:
    key(dict): normalized key, i.e. values must be lists of str
    raises_error(bool): if True (default),
        ValueError is raised if at least one value within key
        is not in the (unconstrained) codes. Otherwise, False is returned.
        If all values from key are in the respective code list,
        True is returned

        return True if key satisfies all constraints. Otherwise, return False or
        raise ValueError, depending on the value of ``raise_error``
        '''
        # validate key against unconstrained codelists
        self._in_codes(key, raise_error)
        # Validate key against constraints if any
        invalid = defaultdict(list)
        for k, values in key.items():
            for v in values:
                if v not in self._constrained_codes[k]:
                    invalid[k].append(v)
        if invalid:
            if raise_error:
                raise ValueError(
                    'Value(s) not in constrained codelists.', invalid)
            else:
                return False
        return True


class CodelistHandler(KeyValidatorMixin):
    '''
    High-level API implementing the
    application of content constraints to codelists. It is primarily
    used as a mixin to StructureMessage instances containing codelists,
    a DSD, Dataflow and related constraints. However, it
    may also be used stand-online. It computes
    the constrained codelists in collaboration with 
    Constrainable, ContentConstraint and Cube Region classes. 
    '''

    def __init__(self, *args, **kwargs):
        '''
        Prepare computation of constrained codelists using the
        cascading mechanism described in Chap. 8 of the Technical Guideline (Part 6 of the SDMX 2.1 standard)

        args:

            constrainables(list of model.Constrainable instances): 
                Constrainable artefacts in descending order sorted by 
                cascading level (e.g., `[DSD, Dataflow]`). At position 0 
                there must be the DSD. Defaults to []. 
                If not given, try to
                collect the constrainables from the StructureMessage. 
                this will be the most common use case. 
        '''
        super(CodelistHandler, self).__init__(*args, **kwargs)
        constrainables = kwargs.get('constrainables', [])
        if constrainables:
            self.__constrainables = constrainables
        elif (hasattr(self, 'datastructure')
              and hasattr(self, 'codelist')):
            self.in_codes = self._in_codes
            if hasattr(self, 'constraint'):
                self.in_constraints = self._in_constraints
            else:
                self.in_constraints = self.in_codes

    @property
    def _constrainables(self):
        if not hasattr(self, '__constrainables'):
            self.__constrainables = []
            # Collecting any constrainables from the StructureMessage
            # is only meaningful if the Message contains but one DataFlow and
            # DSD.
            if (hasattr(self, 'datastructure') and len(self.datastructure) == 1):
                dsd = self.datastructure.aslist()[0]
                self.__constrainables.append(dsd)
                if hasattr(self, 'dataflow'):
                    flow = self.dataflow.aslist()[0]
                    self.__constrainables.append(flow)
                if hasattr(self, 'provisionagreement'):
                    for p in self.provisionagreement.values():
                        if flow in p.constrained_by:
                            self.__constrainables.append(p)
                            break
        return self.__constrainables

    @property
    def _dim_ids(self):
        '''
        Collect the IDs of dimensions which are 
        represented by codelists (this excludes TIME_PERIOD etc.)
        '''
        if not hasattr(self, '__dim_ids'):
            self.__dim_ids = tuple(d.id for d in self._constrainables[0].dimensions.aslist()
                                   if d.local_repr.enum)
        return self.__dim_ids

    @property
    def _attr_ids(self):
        '''
        Collect the IDs of attributes which are 
        represented by codelists 
        '''
        if not hasattr(self, '__attr_ids'):
            self.__attr_ids = tuple(d.id for d in self._constrainables[0].attributes.aslist()
                                    if d.local_repr.enum)
        return self.__attr_ids

    @property
    def _dim_codes(self):
        '''
        Cached property returning a DictLike mapping dim ID's from the DSD to
        frozensets containing all code IDs from the codelist
        referenced by the Concept describing the respective dimensions.
        '''
        if not hasattr(self, '__dim_codes'):
            if self._constrainables:
                enum_components = [d for d in self._constrainables[0].dimensions.aslist()
                                   if d.local_repr.enum]
                self.__dim_codes = DictLike({d.id: frozenset(d.local_repr.enum())
                                             for d in enum_components})
            else:
                self.__dim_codes = {}
        return self.__dim_codes

    @property
    def _attr_codes(self):
        '''
        Cached property returning a DictLike mapping attribute ID's from the DSD to
        frozensets containing all code IDs from the codelist
        referenced by the Concept describing the respective attributes.
        '''
        if not hasattr(self, '__attr_codes'):
            if self._constrainables:
                enum_components = [d for d in self._constrainables[0].attributes.aslist()
                                   if d.local_repr.enum]
                self.__attr_codes = DictLike({d.id: frozenset(d.local_repr.enum())
                                              for d in enum_components})
            else:
                self.__attr_codes = {}
        return self.__attr_codes

    @property
    def _constrained_codes(self):
        '''
        Cached property returning a DictLike mapping dim ID's from the DSD to
        frozensets containing the code IDs from the codelist
        referenced by the Concept for the dimension after applying
        all content constraints to the codelists. Those contenten constraints are
        retrieved pursuant to an implementation of the algorithm described in the
        SDMX 2.1 Technical Guidelines (Part 6) Chap. 9. Hence, constraints
        may constrain the DSD, dataflow definition or provision-agreement.
        '''
        if not hasattr(self, '__constrained_codes'):
            # Run the cascadation mechanism from Chap. 8 of the SDMX 2.1
            # Technical Guidelines.
            cur_dim_codes, cur_attr_codes = self._dim_codes, self._attr_codes
            for c in self._constrainables:
                cur_dim_codes, cur_attr_codes = c.apply(
                    cur_dim_codes, cur_attr_codes)
            self.__constrained_codes = DictLike(cur_dim_codes)
            self.__constrained_codes.update(cur_attr_codes)
        return self.__constrained_codes


class Constraint(MaintainableArtefact):

    def __init__(self, *args, **kwargs):
        super(Constraint, self).__init__(*args, **kwargs)
        self.constraint_attachment = self._reader.read_instance(
            Ref, self, offset='constraint_attachment')


class ContentConstraint(Constraint):

    def __init__(self, *args, **kwargs):
        super(ContentConstraint, self).__init__(*args, **kwargs)
        self.cube_region = self._reader.read_instance(
            CubeRegion, self, first_only=False)

    def apply(self, dim_codes=None, attr_codes=None):
        '''
        Compute the constrained code lists as frozensets by
        merging the constraints resulting from all cube regions into a dict of sets of valid codes 
        for dimensions and attributes respectively.
        We assume that each codelist is constrained by at most one cube
        region so that no set operations are required.

        Return tuple of constrained_dimension_codes(dict), constrained_attribute_codes(dict)
        '''
        dimension, attribute = {}, {}
        for c in self.cube_region:
            d, a = c.apply(dim_codes, attr_codes)
            if d:
                dimension.update(d)
            if a:
                attribute.update(a)
        return dimension, attribute


class KeyValue(SDMXObject):

    def __init__(self, *args, **kwargs):
        super(KeyValue, self).__init__(*args, **kwargs)
        self.id = self._reader.read_as_str('id', self)

    @property
    def values(self):
        if not hasattr(self, '_values'):
            self._values = frozenset(
                self._reader.read_as_str('value', self, first_only=False)) or frozenset()
        return self._values


class CubeRegion(SDMXObject):

    def __init__(self, *args, **kwargs):
        '''
        Get the KeyValues and other attributes.
                '''
        super(CubeRegion, self).__init__(*args, **kwargs)
        self.include = str2bool(self._reader.read_as_str('include', self))
        # get any key-values for dimensions
        self.dimension = {kv.id: kv.values
                          for kv in (self._reader.read_instance(KeyValue, self,
                                                                first_only=False) or [])}
        # get any key-values for attributes
        self.attribute = {kv.id: kv.values
                          for kv in (self._reader.read_instance(KeyValue, self,
                                                                first_only=False, offset='cuberegion_attribute') or [])}

    def apply(self, dim_codes=None, attr_codes=None):
        '''
        Compute the code lists constrained by
        the cube region as frozensets.

        args:
            dim_codes(dict): maps dim IDs to 
                the referenced codelist represented by a frozenset.
                The set may or may not be constrained by a jigher-level
                ContentConstraint. See the 
                Technical Guideline (Part 6 of the SDMX Standard). Default is None (disregard dimensions)
            attr_codes(dict): same as above, but for attributes as 
                specified by a DSD.

        Return tuple of constrained_dimensions(dict), constrained_attribute_codes(dict)
        '''
        dimension = attribute = None
        if dim_codes:
            dimension = {k: (self.dimension[k] & dim_codes[k])
                         for k in self.dimension}
            if not self.include:
                for k, v in dimension.items():
                    dimension[k] = dim_codes[k] - v
        if attr_codes:
            attribute = {k: (self.attribute[k] & attr_codes[k])
                         for k in self.attribute}
            if not self.include:
                for k, v in attribute.items():
                    attribute[k] = attr_codes[k] - v
        return dimension, attribute


class Category(Item):

    def __iter__(self):
        '''
        Return an iterator over the categorised objects
        '''
        m = self._reader.message
        # We assume that only dataflow definitions are categorised.
        resource = m.dataflow
        idx = (self._reader.read_as_str('cat_scheme_id', self), self.id)
        return (resource[c.artefact.id] for c in m._categorisation[idx])


class CategoryScheme(ItemScheme):
    _get_items = Category


class Categorisations(SDMXObject, DictLike):

    def __init__(self, *args, **kwargs):
        super(Categorisations, self).__init__(*args, **kwargs)
        # Group categorisations by categoryscheme id and category id
        # Each group is represented by a list.
        result = defaultdict(list)
        for c in self._reader.read_instance(
                Categorisation, self, first_only=False):
            key = (c.categorised_by.maintainable_parent_id,
                   c.categorised_by.id)
            result[key].append(c)
        self.update(result)


class Ref(SDMXObject):
    # mappings used for resolving the ref
    _cls2rc_name = {
        'Dataflow': 'dataflow',
        'Codelist': 'codelist',
        'DataStructure': 'datastructure',
        'ProvisionAgreement': 'provisionagreement'}

    def __str__(self):
        return ' | '.join(
            (self.__class__.__name__, self.agency_id, self.package, self.id))

    @property
    def package(self):
        return self._reader.read_as_str('ref_package', self)

    @property
    def id(self):
        return self._reader.read_as_str('id', self)

    @property
    def ref_class(self):
        return self._reader.read_as_str('ref_class', self)

    @property
    def version(self):
        return self._reader.read_as_str('ref_version', self)

    @property
    def agency_id(self):
        return self._reader.read_as_str('agencyID', self)

    @property
    def maintainable_parent_id(self):
        return self._reader.read_as_str('maintainable_parent_id', self)

    def __call__(self, request=False, target_only=True, **kwargs):
        '''
        Resolv reference.

        args:

            request(bool): If True (defaut: False), and
                the referenced artefact is not in the same message,
                a request to the data provider will be made to
                fetch it. It will use the
                current Request instance. Thus, requests to
                other agencies are not supported.
            response(bool): If False (default), only the referenced artefact 
                will be returned, otherwise the requested Response instance. Ignored if `request` is False. 
                The latter is useful if writing to pandas is intended.

            kwargs: are passed on to Request.get(). 

        return referenced artefact or entire Response if requested via http, 
            or None if artefact was not found in the current message. 
        '''
        rc_name = self._cls2rc_name[self.ref_class]
        try:
            rc = getattr(self._reader.message, rc_name)
            if self.maintainable_parent_id:
                rc = rc[self.maintainable_parent_id]
            return rc[self.id]
        except (AttributeError, TypeError):
            # Raise error if kwargs is non-empty while no request is made.
            # This is most likely not intended by the caller.
            if not request and kwargs:
                raise ValueError('''Reference target not found in the current message, 
                but ``request`` is False. Yet, kwargs to be passed 
                on to the request were given: {0}'''.format(kwargs))
            if request:
                req = self._reader.request
                resp = req.get(resource_type=rc_name,
                               resource_id=self.maintainable_parent_id or self.id,
                               agency=self.agency_id, **kwargs)
                if target_only:
                    rc = getattr(resp.msg, rc_name)
                    return rc[self.id]
                else:
                    return resp
            else:
                return None


class Categorisation(MaintainableArtefact):

    def __init__(self, *args, **kwargs):
        super(Categorisation, self).__init__(*args, **kwargs)
        self.categorised_by = self._reader.read_instance(
            Ref, self, offset='ref_target')
        self.artefact = self._reader.read_instance(
            Ref, self, offset='ref_source')


class DataflowDefinition(Constrainable, StructureUsage):
    pass


class ProvisionAgreement(Constrainable, MaintainableArtefact):

    def __init__(self, *args, **kwargs):
        super(ProvisionAgreement, self).__init__(*args, **kwargs)
        self.structure_usage = self._reader.read_instance(
            Ref, self, offset='structure_usage')


class DataAttribute(Component):

    @property
    def related_to(self):
        return self._reader.read_instance(Ref, self).id

    # fix this
    # role = Instance(Concept)

    @property
    def usage_status(self):
        return self._reader.read_as_str('assignment_status', self)


class DataStructureDefinition(Constrainable, MaintainableArtefact):

    def __init__(self, *args, **kwargs):
        super(DataStructureDefinition, self).__init__(*args, **kwargs)
        self.dimensions = self._reader.read_instance(DimensionDescriptor, self)
        self.measures = self._reader.read_instance(MeasureDescriptor, self)
        self.attributes = self._reader.read_instance(AttributeDescriptor, self)


class Dimension(Component):
    # role = Instance(Concept)

    def __init__(self, *args, **kwargs):
        super(Dimension, self).__init__(*args, **kwargs)
        self._position = int(self._reader.read_as_str('position', self))


class TimeDimension(Dimension):
    pass
    # role must be None. Enforce this in future versions.


class MeasureDimension(Dimension):
    pass
    # representation: must be concept scheme and local, i.e. no
    # inheritance from concept


class DimensionDescriptor(ComponentList):
    _get_items = Dimension
    _sort_key = attrgetter('_position')

    def __init__(self, *args, **kwargs):
        super(DimensionDescriptor, self).__init__(*args, **kwargs)
        # add time_dimension and measure_dimension to the scheme
        self._reader.read_identifiables(TimeDimension, self)
        self._reader.read_identifiables(MeasureDimension, self)


class PrimaryMeasure(Component):
    pass


class MeasureDescriptor(ComponentList):
    _get_items = PrimaryMeasure


class AttributeDescriptor(ComponentList):
    _get_items = DataAttribute


class ReportingYearStartDay(DataAttribute):
    pass


class DataSet(SDMXObject):

    #     reporting_begin = Any
    #     reporting_end = Any
    #     valid_from = Any
    #     valid_to = Any
    #     data_extraction_date = Any
    #     publication_year = Any
    #     publication_period = Any
    #     set_id = Unicode
    #     action = Enum(('update', 'append', 'delete'))
    #     described_by = Instance(DataflowDefinition)
    #     structured_by = Instance(DataStructureDefinition)
    #     published_by = Any
    #     attached_attribute = Any

    def __init__(self, *args, **kwargs):
        super(DataSet, self).__init__(*args, **kwargs)
        self._attrib = self._groups = None

    @property
    def groups(self):
        if not self._groups:
            self._groups = tuple(self.iter_groups)
        return self._groups

    @property
    def attrib(self):
        if not self._attrib:
            self._attrib = self._reader.dataset_attrib(self)
        return self._attrib

    @property
    def dim_at_obs(self):
        return self._reader.dim_at_obs(self)

    def obs(self, with_values=True, with_attributes=True):
        '''
        return an iterator over observations in a flat dataset.
        An observation is represented as a namedtuple with 3 fields ('key', 'value', 'attrib').

        obs.key is a namedtuple of dimensions. Its field names represent dimension names,
        its values the dimension values.

        obs.value is a string that can in in most cases be interpreted as float64
        obs.attrib is a namedtuple of attribute names and values.

        with_values and with_attributes: If one or both of these flags
        is False, the respective value will be None. Use these flags to
        increase performance. The flags default to True.
        '''
        # distinguish between generic and structure-specific observations
        # only generic ones are currently implemented.
        return self._reader.iter_generic_obs(
            self, with_values, with_attributes)

    @property
    def series(self):
        '''
        return an iterator over Series instances in this DataSet.
        Note that DataSets in flat format, i.e.
        header.dim_at_obs = "AllDimensions", have no series. Use DataSet.obs() instead.
        '''
        return self._reader.iter_series(self)

    @property
    def iter_groups(self):
        return self._reader.generic_groups(self)


class Series(SDMXObject):

    def __init__(self, *args, **kwargs):
        super(Series, self).__init__(*args)
        self.key = self._reader.series_key(self)
        self.attrib = self._reader.series_attrib(self)
        dataset = kwargs.get('dataset')
        if not isinstance(dataset, DataSet):
            raise TypeError("'dataset' must be a DataSet instance, got %s"
                            % dataset.__class__.__name__)
        self.dataset = dataset

    @property
    def group_attrib(self):
        '''
        return a namedtuple containing all attributes attached
        to groups of which the given series is a member
        for each group of which the series is a member
        '''
        group_attributes = [g.attrib for g in self.dataset.groups if self in g]
        if group_attributes:
            return concat_namedtuples(*group_attributes)

    def obs(self, with_values=True, with_attributes=True, reverse_obs=False):
        '''
        return an iterator over observations in a series.
        An observation is represented as a namedtuple with 3 fields ('key', 'value', 'attrib').
        obs.key is a namedtuple of dimensions, obs.value is a string value and
        obs.attrib is a namedtuple of attributes. If with_values or with_attributes
        is False, the respective value is None. Use these flags to
        increase performance. The flags default to True.
        '''
        return self._reader.iter_generic_series_obs(self,
                                                    with_values, with_attributes, reverse_obs)


class Group(SDMXObject):

    def __init__(self, *args, **kwargs):
        super(Group, self).__init__(*args, **kwargs)
        self.key = self._reader.group_key(self)
        self.attrib = self._reader.series_attrib(self)

    def __contains__(self, series):
        group_key, series_key = self.key, series.key
        for f in group_key._fields:
            if getattr(group_key, f) != getattr(series_key, f):
                return False
        return True


class Message(SDMXObject):
    # Describe supported message content as 4-tuples of the form
    # (attribute_name, reader_method_name,
    # class_object_to_be_instantiated, optional_offset_path_name)
    _content_types = [
        ('header', 'read_instance', Header, None),
        ('footer', 'read_instance', Footer, None)]

    def __init__(self, *args, **kwargs):
        super(Message, self).__init__(*args, **kwargs)
        # Initialize data attributes for which the response contains payload
        for name, method, cls, offset in self._content_types:
            payload = getattr(
                self._reader, method)(cls, self, offset=offset)
            if payload:
                setattr(self, name, payload)


class StructureMessage(CodelistHandler, Message):
    _content_types = Message._content_types[:]
    _content_types.extend([
        ('constraint', 'read_identifiables', ContentConstraint, None),
        ('codelist', 'read_identifiables', Codelist, None),
        ('conceptscheme', 'read_identifiables', ConceptScheme, None),
        ('dataflow', 'read_identifiables', DataflowDefinition,
         'dataflow_from_msg'),
        ('datastructure', 'read_identifiables',
         DataStructureDefinition, None),
        ('provisionagreement', 'read_identifiables',
            ProvisionAgreement, None),
        ('categoryscheme', 'read_identifiables', CategoryScheme, None),
        ('_categorisation', 'read_instance', Categorisations, None)])


class DataMessage(KeyValidatorMixin, Message):
    _content_types = Message._content_types[:]
    _content_types.extend([
        ('data', 'read_instance', DataSet, None)])

    def __init__(self, *args, **kwargs):
        super(DataMessage, self).__init__(*args, **kwargs)
        # As series keys always reflect constrained codelists, we equate both methods
        # inherited from KeyValidatorMixin for API compatibility.
        # the _in_constraints methods must not be used.
        self.in_codes = self._in_codes
        self.in_constraints = self._in_codes

    @property
    def _dim_ids(self):
        '''
        Return a tuple of dimension IDs gleened from the
        first Series in the dataset.
        '''
        if not hasattr(self, '__dim_ids'):
            self.__dim_ids = next(self.data.series).key._fields
        return self.__dim_ids

    @property
    def _dim_codes(self):
        '''
        Cached property returning a DictLike mapping dim ID's gleened from
        the key attribute of the first series in the dataset to
        frozensets containing all code IDs occurring in the dataset.
        The result is identical to the homonymous methods of :class:`StructureMessage` if
        and only if the dataset was requested with 'serieskeyonly=True`. To do this,
        use an agency which supports this feature and enable it
        by passing 'series_keys=True' to the get() method of the Request
        instance.
        '''
        if not hasattr(self, '__dim_codes'):
            keys = (s.key for s in self.data.series)
            self.__dim_codes = DictLike({dim_id: frozenset(codes)
                                         for dim_id, codes in zip(self._dim_ids, zip(*keys))})
        return self.__dim_codes

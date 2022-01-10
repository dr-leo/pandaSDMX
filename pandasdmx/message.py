"""Classes for SDMX messages.

:class:`Message` and related classes are not defined in the SDMX
:doc:`information model <implementation>`, but in the :ref:`SDMX-ML standard <formats>`.

:mod:`sdmx` also uses :class:`DataMessage` to encapsulate SDMX-JSON data returned by
data sources.
"""
import logging
from datetime import datetime
from typing import Any, List, Optional, Text, Union

from pandasdmx import model
from pandasdmx.util import (
    BaseModel,
    DictLike,
    compare,
    dictlike_field,
    direct_fields,
    get_args,
    summarize_dictlike,
    validate_dictlike,
)

log = logging.getLogger(__name__)


def _summarize(obj, fields):
    """Helper method for __repr__ on Header and Message (sub)classes."""
    for name in fields:
        attr = getattr(obj, name)
        if attr is None:
            continue
        elif isinstance(attr, datetime):
            attr = attr.isoformat()
        yield f"{name}: {repr(attr)}"


class Header(BaseModel):
    """Header of an SDMX-ML message.

    SDMX-JSON messages do not have headers.
    """

    #: (optional) Error code for the message.
    error: Optional[Text] = None
    #: Date and time at which the data was extracted.
    extracted: Optional[datetime] = None
    #: Identifier for the message.
    id: Optional[Text] = None
    #: Date and time at which the message was generated.
    prepared: Optional[datetime] = None
    #: Start of the time period covered by a :class:`.DataMessage`.
    reporting_begin: Optional[datetime] = None
    #: End of the time period covered by a :class:`.DataMessage`.
    reporting_end: Optional[datetime] = None
    #: Intended recipient of the message, e.g. the user's name for an
    #: authenticated service.
    receiver: Optional[model.Agency] = None
    #: The :class:`.Agency` associated with the data :class:`~.source.Source`.
    sender: Optional[model.Agency] = None
    #:
    source: model.InternationalString = model.InternationalString()
    #:
    test: bool = False

    def __repr__(self):
        """String representation."""
        lines = ["<Header>"]
        lines.extend(_summarize(self, self.__fields__.keys()))
        return "\n  ".join(lines)

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two Headers are the same if their corresponding attributes are equal.

        Parameters
        ----------
        strict : bool, optional
            Passed to :func:`.compare`.
        """
        return all(compare(f, self, other, strict) for f in self.__fields__.keys())


class Footer(BaseModel):
    """Footer of an SDMX-ML message.

    SDMX-JSON messages do not have footers.
    """

    #:
    severity: Optional[str] = None
    #: The body text of the Footer contains zero or more blocks of text.
    text: List[model.InternationalString] = []
    #:
    code: Optional[int] = None

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two Footers are the same if their :attr:`code`, :attr:`severity`, and
        :attr:`text` are equal.

        Parameters
        ----------
        strict : bool, optional
            Passed to :func:`.compare`.
        """
        return all(compare(f, self, other, strict) for f in self.__fields__.keys())


class Message(BaseModel):
    class Config:
        # for .response
        arbitrary_types_allowed = True

    #: :class:`Header` instance.
    header: Header = Header()
    #: (optional) :class:`Footer` instance.
    footer: Optional[Footer] = None
    #: :class:`requests.Response` instance for the response to the HTTP request that
    #: returned the Message. This is not part of the SDMX standard.
    response: Optional[Any] = None

    def __str__(self):
        return repr(self)

    def __repr__(self):
        """String representation."""
        lines = [
            f"<pandasdmx.{self.__class__.__name__}>",
            repr(self.header).replace("\n", "\n  "),
        ]
        lines.extend(_summarize(self, ["footer", "response"]))
        return "\n  ".join(lines)

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two Messages are the same if their :attr:`header` and :attr:`footer` compare
        equal.

        Parameters
        ----------
        strict : bool, optional
            Passed to :func:`.compare`.
        """
        return self.header.compare(other.header, strict) and (
            self.footer is other.footer is None
            or self.footer.compare(other.footer, strict)
        )


class ErrorMessage(Message):
    pass


@validate_dictlike
class StructureMessage(Message):
    #: Collection of :class:`.Categorisation`.
    categorisation: DictLike[str, model.Categorisation] = dictlike_field()
    #: Collection of :class:`.CategoryScheme`.
    category_scheme: DictLike[str, model.CategoryScheme] = dictlike_field()
    #: Collection of :class:`.Codelist`.
    codelist: DictLike[str, model.Codelist] = dictlike_field()
    #: Collection of :class:`.ConceptScheme`.
    concept_scheme: DictLike[str, model.ConceptScheme] = dictlike_field()
    #: Collection of :class:`.ContentConstraint`.
    constraint: DictLike[str, model.ContentConstraint] = dictlike_field()
    #: Collection of :class:`.DataflowDefinition`.
    dataflow: DictLike[str, model.DataflowDefinition] = dictlike_field()
    #: Collection of :class:`.DataStructureDefinition`.
    structure: DictLike[str, model.DataStructureDefinition] = dictlike_field()
    #: Collection of :class:`.AgencyScheme`.
    organisation_scheme: DictLike[str, model.AgencyScheme] = dictlike_field()
    #: Collection of :class:`.ProvisionAgreement`.
    provisionagreement: DictLike[str, model.ProvisionAgreement] = dictlike_field()

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two StructureMessages compare equal if :meth:`.DictLike.compare` is :obj:`True`
        for each of the object collection attributes.

        Parameters
        ----------
        strict : bool, optional
            Passed to :meth:`.DictLike.compare`.
        """
        return super().compare(other, strict) and all(
            getattr(self, f).compare(getattr(other, f), strict)
            for f in direct_fields(self.__class__).keys()
        )

    def add(self, obj: model.IdentifiableArtefact):
        """Add `obj` to the StructureMessage."""
        for field, field_info in direct_fields(self.__class__).items():
            # NB for some reason mypy complains here, but not in __contains__(), below
            if isinstance(
                obj,
                get_args(field_info.outer_type_)[1],  # type: ignore [attr-defined]
            ):
                getattr(self, field)[obj.id] = obj
                return
        raise TypeError(type(obj))

    def get(
        self, obj_or_id: Union[str, model.IdentifiableArtefact]
    ) -> Optional[model.IdentifiableArtefact]:
        """Retrieve `obj_or_id` from the StructureMessage.

        Parameters
        ----------
        obj_or_id : str or .IdentifiableArtefact
            If an IdentifiableArtefact, return an object of the same class and
            :attr:`~.IdentifiableArtefact.id`; if :class:`str`, an object with this ID.

        Returns
        -------
        .IdentifiableArtefact
            with the given ID and possibly class.
        None
            if there is no match.

        Raises
        ------
        ValueError
            if `obj_or_id` is a string and there are ≥2 objects (of different classes)
            with the same ID.
        """
        id = (
            obj_or_id.id
            if isinstance(obj_or_id, model.IdentifiableArtefact)
            else obj_or_id
        )

        candidates: List[model.IdentifiableArtefact] = list(
            filter(
                None,
                map(
                    lambda f: getattr(self, f).get(id),
                    direct_fields(self.__class__).keys(),
                ),
            )
        )

        if len(candidates) > 1:
            raise ValueError(f"ambiguous; {repr(obj_or_id)} matches {repr(candidates)}")

        return candidates[0] if len(candidates) == 1 else None

    def objects(self, cls):
        """Get a reference to the attribute for objects of type `cls`.

        For example, if `cls` is the class :class:`DataStructureDefinition` (not an
        instance), return a reference to :attr:`structure`.
        """
        for name, info in direct_fields(self.__class__).items():
            if issubclass(cls, info.sub_fields[0].type_):
                return getattr(self, name)
        raise TypeError(cls)

    def __contains__(self, item):
        """Return :obj:`True` if `item` is in the StructureMessage."""
        for field, field_info in direct_fields(self.__class__).items():
            if isinstance(item, get_args(field_info.outer_type_)[1]):
                return item in getattr(self, field).values()
        raise TypeError(f"StructureMessage has no collection of {type(item)}")

    def __repr__(self):
        """String representation."""
        lines = [super().__repr__()]

        # StructureMessage contents
        for attr in self.__dict__.values():
            if isinstance(attr, DictLike) and attr:
                lines.append(summarize_dictlike(attr))

        return "\n  ".join(lines)


class DataMessage(Message):
    """Data Message.

    .. note:: A DataMessage may contain zero or more :class:`.DataSet`, so
       :attr:`data` is a list. To retrieve the first (and possibly only)
       data set in the message, access the first element of the list:
       ``msg.data[0]``.
    """

    #: :class:`list` of :class:`.DataSet`.
    data: List[model.DataSet] = []
    #: :class:`.DataflowDefinition` that contains the data.
    dataflow: model.DataflowDefinition = model.DataflowDefinition()
    #: The "dimension at observation level".
    observation_dimension: Optional[
        Union[
            model._AllDimensions,
            model.DimensionComponent,
            List[model.DimensionComponent],
        ]
    ] = None

    # Convenience access
    @property
    def structure(self):
        """DataStructureDefinition used in the :attr:`dataflow`."""
        return self.dataflow.structure

    def __repr__(self):
        """String representation."""
        lines = [super().__repr__()]

        # DataMessage contents
        if self.data:
            lines.append("DataSet ({})".format(len(self.data)))
        lines.extend(_summarize(self, ("dataflow", "observation_dimension")))

        return "\n  ".join(lines)

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two DataMessages are the same if:

        - :meth:`.Message.compare` is :obj:`True`
        - their :attr:`dataflow` and :attr:`observation_dimension` compare equal.
        - they have the same number of :class:`DataSets <DataSet>`, and
        - corresponding DataSets compare equal (see :meth:`.DataSet.compare`).

        Parameters
        ----------
        strict : bool, optional
            Passed to :func:`.compare`.
        """
        return (
            super().compare(other, strict)
            and compare("dataflow", self, other, strict)
            and compare("observation_dimension", self, other, strict)
            and len(self.data) == len(other.data)
            and all(ds[0].compare(ds[1], strict) for ds in zip(self.data, other.data))
        )

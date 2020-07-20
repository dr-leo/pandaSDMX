import logging

import pandasdmx.format.protobuf_pb2 as pb

log = logging.getLogger(__name__)


def write(obj, *args, **kwargs):
    """Convert an SDMX *obj* to protobuf string."""
    return _write(obj, *args, **kwargs).SerializeToString()


def _write(obj, *args, **kwargs):
    """Helper for :meth:`write`; returns :mod:`protobuf` object(s)."""
    cls_name = obj.__class__.__name__
    func_name = f"write_{cls_name.lower()}"
    try:
        func = globals()[func_name]
    except KeyError:
        raise NotImplementedError(f"write {cls_name} to protobuf")
    else:
        return func(obj, *args, **kwargs)


def _copy(obj, pb_obj):
    """Update the attributes of *pb_obj* from the sdmx.message/.model *obj*."""
    dir_logged = False

    for attr, value in obj.__dict__.items():
        if not value:
            continue

        try:
            setattr(pb_obj, attr, value)
            log.info(f"Set {attr}")
        except Exception as exc:
            log.error(f"Failed to set {attr}: {exc}")

            if not dir_logged:
                fields = filter(lambda n: not n.startswith("_"), dir(pb_obj))
                log.info(sorted(fields))
                dir_logged = True


def write_structuremessage(obj, *args, **kwargs):
    envelope = pb.Envelope()

    for cl in obj.codelist.values():
        pb_obj = envelope.data.codelists.add()
        _copy(cl, pb_obj)

    return envelope

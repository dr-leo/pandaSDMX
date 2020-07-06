============================= test session starts =============================
platform win32 -- Python 3.7.6, pytest-5.3.0, py-1.8.1, pluggy-0.13.1
rootdir: C:\Users\a3305\documents\github\pandasdmx, inifile: pytest.ini
plugins: cov-2.8.1, remotedata-0.3.2, requests-mock-1.7.0
collected 329 items / 82 deselected / 247 selected

pandasdmx\tests\test_api.py FFF                                          [  1%]
pandasdmx\tests\test_compat.py F                                         [  1%]
pandasdmx\tests\test_dataset.py ...F..FF..F..F                           [  7%]
pandasdmx\tests\test_dataset_bare.py FF                                  [  8%]
pandasdmx\tests\test_dataset_ss.py EEEEEEEEEEEEEEEEEEEEEEEEE             [ 18%]
pandasdmx\tests\test_docs.py F                                           [ 18%]
pandasdmx\tests\test_dsd.py ...F......F                                  [ 23%]
pandasdmx\tests\test_experimental.py .                                   [ 23%]
pandasdmx\tests\test_insee.py FFF                                        [ 24%]
pandasdmx\tests\test_message.py FFFF                                     [ 26%]
pandasdmx\tests\test_model.py ...............                            [ 32%]
pandasdmx\tests\test_performance.py .                                    [ 32%]
pandasdmx\tests\test_remote.py s                                         [ 33%]
pandasdmx\tests\test_source.py ...                                       [ 34%]
pandasdmx\tests\test_util.py ..                                          [ 35%]
pandasdmx\tests\format\test_xml.py .                                     [ 35%]
pandasdmx\tests\reader\test_json.py ......                               [ 38%]
pandasdmx\tests\reader\test_reader_xml.py .............................. [ 50%]
.....................                                                    [ 58%]
pandasdmx\tests\writer\test_pandas.py F................................. [ 72%]
..................................FFFFFFFFFFFFFFFFFFF.                   [ 94%]
pandasdmx\tests\writer\test_protobuf.py x                                [ 94%]
pandasdmx\tests\writer\test_writer_xml.py FFFFFsFFFFFFF                  [100%]

=================================== ERRORS ====================================
_________________ ERROR at setup of TestFlatDataSet.test_msg __________________

self = <pandasdmx.tests.test_dataset_ss.TestFlatDataSet object at 0x000001DEF72884C8>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
____________ ERROR at setup of TestFlatDataSet.test_structured_by _____________

self = <pandasdmx.tests.test_dataset_ss.TestFlatDataSet object at 0x000001DEF72884C8>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
_______________ ERROR at setup of TestFlatDataSet.test_msg_type _______________

self = <pandasdmx.tests.test_dataset_ss.TestFlatDataSet object at 0x000001DEF72884C8>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
_____________ ERROR at setup of TestFlatDataSet.test_dataset_cls ______________

self = <pandasdmx.tests.test_dataset_ss.TestFlatDataSet object at 0x000001DEF72884C8>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
_____________ ERROR at setup of TestFlatDataSet.test_generic_obs ______________

self = <pandasdmx.tests.test_dataset_ss.TestFlatDataSet object at 0x000001DEF72884C8>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
_____________ ERROR at setup of TestFlatDataSet.test_write2pandas _____________

self = <pandasdmx.tests.test_dataset_ss.TestFlatDataSet object at 0x000001DEF72884C8>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
________________ ERROR at setup of TestSeriesDataSet.test_msg _________________

self = <pandasdmx.tests.test_dataset_ss.TestSeriesDataSet object at 0x000001DEF727AD48>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
___________ ERROR at setup of TestSeriesDataSet.test_structured_by ____________

self = <pandasdmx.tests.test_dataset_ss.TestSeriesDataSet object at 0x000001DEF727AD48>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
______________ ERROR at setup of TestSeriesDataSet.test_msg_type ______________

self = <pandasdmx.tests.test_dataset_ss.TestSeriesDataSet object at 0x000001DEF727AD48>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
____________ ERROR at setup of TestSeriesDataSet.test_dataset_cls _____________

self = <pandasdmx.tests.test_dataset_ss.TestSeriesDataSet object at 0x000001DEF727AD48>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
________________ ERROR at setup of TestSeriesDataSet.test_obs _________________

self = <pandasdmx.tests.test_dataset_ss.TestSeriesDataSet object at 0x000001DEF727AD48>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
_______________ ERROR at setup of TestSeriesDataSet.test_pandas _______________

self = <pandasdmx.tests.test_dataset_ss.TestSeriesDataSet object at 0x000001DEF727AD48>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
____________ ERROR at setup of TestSeriesDataSet.test_write2pandas ____________

self = <pandasdmx.tests.test_dataset_ss.TestSeriesDataSet object at 0x000001DEF727AD48>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
________________ ERROR at setup of TestSeriesDataSet2.test_msg ________________

self = <pandasdmx.tests.test_dataset_ss.TestSeriesDataSet2 object at 0x000001DEF727AD08>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
___________ ERROR at setup of TestSeriesDataSet2.test_structured_by ___________

self = <pandasdmx.tests.test_dataset_ss.TestSeriesDataSet2 object at 0x000001DEF727AD08>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
_____________ ERROR at setup of TestSeriesDataSet2.test_msg_type ______________

self = <pandasdmx.tests.test_dataset_ss.TestSeriesDataSet2 object at 0x000001DEF727AD08>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
____________ ERROR at setup of TestSeriesDataSet2.test_dataset_cls ____________

self = <pandasdmx.tests.test_dataset_ss.TestSeriesDataSet2 object at 0x000001DEF727AD08>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
__________ ERROR at setup of TestSeriesDataSet2.test_structured_obs ___________

self = <pandasdmx.tests.test_dataset_ss.TestSeriesDataSet2 object at 0x000001DEF727AD08>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
_____________ ERROR at setup of TestSeriesDataSet2.test_dataframe _____________

self = <pandasdmx.tests.test_dataset_ss.TestSeriesDataSet2 object at 0x000001DEF727AD08>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
__________ ERROR at setup of TestSeriesData_SiblingGroup_TS.test_msg __________

self = <pandasdmx.tests.test_dataset_ss.TestSeriesData_SiblingGroup_TS object at 0x000001DEF72BC248>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
_____ ERROR at setup of TestSeriesData_SiblingGroup_TS.test_structured_by _____

self = <pandasdmx.tests.test_dataset_ss.TestSeriesData_SiblingGroup_TS object at 0x000001DEF72BC248>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
________ ERROR at setup of TestSeriesData_SiblingGroup_TS.test_groups _________

self = <pandasdmx.tests.test_dataset_ss.TestSeriesData_SiblingGroup_TS object at 0x000001DEF72BC248>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
___________ ERROR at setup of TestSeriesData_RateGroup_TS.test_msg ____________

self = <pandasdmx.tests.test_dataset_ss.TestSeriesData_RateGroup_TS object at 0x000001DEF72C3908>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
______ ERROR at setup of TestSeriesData_RateGroup_TS.test_structured_by _______

self = <pandasdmx.tests.test_dataset_ss.TestSeriesData_RateGroup_TS object at 0x000001DEF72C3908>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
__________ ERROR at setup of TestSeriesData_RateGroup_TS.test_groups __________

self = <pandasdmx.tests.test_dataset_ss.TestSeriesData_RateGroup_TS object at 0x000001DEF72C3908>

    @pytest.fixture(scope="class")
    def dsd(self):
>       yield sdmx.read_sdmx(self.path / self.dsd_filename).structure[0]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_ss.py:22: NameError
================================== FAILURES ===================================
_______________________________ test_read_sdmx ________________________________

tmp_path = WindowsPath('C:/Users/a3305/AppData/Local/Temp/pytest-of-a3305/pytest-4/test_read_sdmx0')

    def test_read_sdmx(tmp_path):
        # Copy the file to a temporary file with an urecognizable suffix
        target = tmp_path / "foo.badsuffix"
        with specimen("flat.json", opened=False) as original:
            target.open("w").write(original.read_text())
    
        # With unknown file extension, read_sdmx() peeks at the file content
>       sdmx.read_sdmx(target)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_api.py:20: NameError
________________________________ test_request _________________________________

    def test_request():
        # Constructor
>       r = sdmx.Request(log_level=logging.ERROR)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_api.py:42: NameError
_________________________ test_request_get_exceptions _________________________

    def test_request_get_exceptions():
        """Tests of Request.get() that don't require remote data."""
>       req = sdmx.Request("ESTAT")
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_api.py:71: NameError
__________________________________ test_xml ___________________________________

    def test_xml():
        """Test that objects have the expected layout with rtype='compat'."""
        # GenericData with non-time Dimension at observation \u2192 data frame
>       df1 = pd_obj("ng-xs.xml")

pandasdmx\tests\test_compat.py:18: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

name = 'ng-xs.xml'

    def pd_obj(name):
        """Return the specimen at *name* read, then converted to pandas."""
        with specimen(name) as f:
>           data_msg = sdmx.read_sdmx(f)
E           NameError: name 'sdmx' is not defined

pandasdmx\tests\test_compat.py:11: NameError
____________________ TestGenericFlatDataSet.test_to_pandas ____________________

self = <pandasdmx.tests.test_dataset.TestGenericFlatDataSet object at 0x000001DEF84B7708>
msg = <pandasdmx.DataMessage>
  <Header>
    id: 'Generic'
    prepared: '2010-01-04T16:21:49+01:00'
    sender: <Agency ECB...DataflowDefinition (missing id)>
  observation_dimension: <pandasdmx.model._AllDimensions object at 0x000001DEF56D0FC8>

    def test_to_pandas(self, msg):
        # Single data series is converted to pd.Series
>       data_series = sdmx.to_pandas(msg.data[0])
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset.py:53: NameError
____________________ TestGenericSeriesDataSet.test_pandas _____________________

self = <pandasdmx.tests.test_dataset.TestGenericSeriesDataSet object at 0x000001DEF84D9F88>
msg = <pandasdmx.DataMessage>
  <Header>
    id: 'Generic'
    prepared: '2010-01-04T16:21:49+01:00'
    sender: <Agency ECB...est: False
  DataSet (1)
  dataflow: <DataflowDefinition (missing id)>
  observation_dimension: <Dimension TIME_PERIOD>

    def test_pandas(self, msg):
        data = msg.data[0]
    
        series_keys = list(data.series.keys())
    
        # Number of series in dataframe
        assert len(series_keys) == 4
    
        # Convert the observations for one SeriesKey to a pd.Series
        s3_key = series_keys[3]
>       s3 = sdmx.to_pandas(data.series[s3_key])
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset.py:114: NameError
_________________ TestGenericSeriesDataSet.test_write2pandas __________________

self = <pandasdmx.tests.test_dataset.TestGenericSeriesDataSet object at 0x000001DEF8505F08>
msg = <pandasdmx.DataMessage>
  <Header>
    id: 'Generic'
    prepared: '2010-01-04T16:21:49+01:00'
    sender: <Agency ECB...est: False
  DataSet (1)
  dataflow: <DataflowDefinition (missing id)>
  observation_dimension: <Dimension TIME_PERIOD>

    def test_write2pandas(self, msg):
>       df = sdmx.to_pandas(msg, attributes="")
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset.py:151: NameError
__________________ TestGenericSeriesDataSet2.test_dataframe ___________________

self = <pandasdmx.tests.test_dataset.TestGenericSeriesDataSet2 object at 0x000001DEF85496C8>
msg = <pandasdmx.DataMessage>
  <Header>
    id: 'Generic'
    prepared: '2010-01-04T16:21:49+01:00'
    sender: <Agency ECB... False
  DataSet (1)
  dataflow: <DataflowDefinition (missing id)>
  observation_dimension: <TimeDimension TIME_PERIOD>

    def test_dataframe(self, msg):
>       df = sdmx.to_pandas(msg.data[0]).iloc[::-1]
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset.py:202: NameError
_______________ TestGenericSeriesData_RateGroup_TS.test_footer ________________

self = <pandasdmx.tests.test_dataset.TestGenericSeriesData_RateGroup_TS object at 0x000001DEF852CA48>

    def test_footer(self):
        with specimen("footer.xml") as f:
>           f = sdmx.read_sdmx(f).footer
E           NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset.py:254: NameError
__________________________________ test_flat __________________________________

    def test_flat():
        # Create a bare Message
        msg = DataMessage()
    
        # Recreate the content from exr-flat.json
        header = Header(
            id="62b5f19d-f1c9-495d-8446-a3661ed24753",
            prepared="2012-11-29T08:40:26Z",
            sender=model.Agency(id="ECB"),
        )
        msg.header = header
    
        ds = DataSet()
    
        # Create a Key and attributes
        key = Key(
            FREQ="D",
            CURRENCY="NZD",
            CURRENCY_DENOM="EUR",
            EXR_TYPE="SP00",
            EXR_SUFFIX="A",
            TIME_PERIOD="2013-01-18",
        )
        obs_status = DataAttribute(id="OBS_STATUS")
        attr = {"OBS_STATUS": AttributeValue(value_for=obs_status, value="A")}
    
        ds.obs.append(Observation(dimension=key, value=1.5931, attached_attribute=attr))
    
        key = key.copy(TIME_PERIOD="2013-01-21")
        ds.obs.append(Observation(dimension=key, value=1.5925, attached_attribute=attr))
    
        key = key.copy(CURRENCY="RUB", TIME_PERIOD="2013-01-18")
        ds.obs.append(Observation(dimension=key, value=40.3426, attached_attribute=attr))
    
        key = key.copy(TIME_PERIOD="2013-01-21")
        ds.obs.append(Observation(dimension=key, value=40.3000, attached_attribute=attr))
    
        msg.data.append(ds)
    
        # Write to pd.Dataframe
>       df1 = sdmx.to_pandas(msg)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_bare.py:50: NameError
______________________________ test_bare_series _______________________________

    def test_bare_series():
        with specimen("ng-ts.xml") as f:
>           sdmx.read_sdmx(f)
E           NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dataset_bare.py:61: NameError
__________________________ test_doc_howto_timeseries __________________________

    def test_doc_howto_timeseries():
        with specimen("sg-ts.xml") as f:
>           ds = sdmx.read_sdmx(f).data[0]
E           NameError: name 'sdmx' is not defined

pandasdmx\tests\test_docs.py:226: NameError
___________________ Test_ESTAT_dsd_apro_mk_cola.test_writer ___________________

self = <pandasdmx.tests.test_dsd.Test_ESTAT_dsd_apro_mk_cola object at 0x000001DEF850EF08>
msg = <pandasdmx.StructureMessage>
  <Header>
    id: 'IDREF34759'
    prepared: '2014-11-29T17:54:51.840Z'
    receiver: <A...L_OBS_STATUS CL_PRODMILK CL...
  ConceptScheme (1): CS_DSD_apro_mk_cola
  DataStructureDefinition (1): DSD_apro_mk_cola

    def test_writer(self, msg):
>       cls_as_dfs = sdmx.to_pandas(msg.codelist)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dsd.py:26: NameError
____________________________ test_exr_constraints _____________________________

    def test_exr_constraints():
        with specimen("1/structure-full.xml") as f:
>           m = sdmx.read_sdmx(f)
E           NameError: name 'sdmx' is not defined

pandasdmx\tests\test_dsd.py:88: NameError
_________________________ TestINSEE.test_load_dataset _________________________

self = <pandasdmx.tests.test_insee.TestINSEE object at 0x000001DEF862B388>
req = <pandasdmx.api.Request object at 0x000001DEF862BB08>

    def test_load_dataset(self, req):
        dataset_code = "IPI-2010-A21"
    
        # Load all dataflows
>       dataflows_response = sdmx.read_sdmx(DATAFLOW_FP)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_insee.py:42: NameError
________________________ TestINSEE.test_fixe_key_names ________________________

self = <pandasdmx.tests.test_insee.TestINSEE object at 0x000001DEF8625A48>
req = <pandasdmx.api.Request object at 0x000001DEF862BB08>

    def test_fixe_key_names(self, req):
        """Verify key or attribute contains '-' in name."""
        dataset_code = "CNA-2010-CONSO-SI-A17"
    
        fp_datastructure = DATASETS[dataset_code]["datastructure-fp"]
>       datastructure_response = sdmx.read_sdmx(fp_datastructure)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_insee.py:89: NameError
___________________ TestINSEE.test_freq_in_series_attribute ___________________

self = <pandasdmx.tests.test_insee.TestINSEE object at 0x000001DEF8483308>
req = <pandasdmx.api.Request object at 0x000001DEF862BB08>

    def test_freq_in_series_attribute(self, req):
        # Test that we don't have regression on Issues #39 and #41
        # INSEE time series provide the FREQ value as attribute on the series
        # instead of a dimension. This caused a runtime error when writing as
        # pandas dataframe.
>       data_response = sdmx.read_sdmx(SERIES["UNEMPLOYMENT_CAT_A_B_C"]["data-fp"])
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\test_insee.py:131: NameError
________________ test_message_repr[IPI-2010-A21-structure.xml] ________________

pattern = 'IPI-2010-A21-structure.xml'
expected = "<sdmx.StructureMessage>\n  <Header>\n    id: 'categorisation_1450864290565'\n    prepared: '2015-12-23T09:51:30.565Z'...ConceptScheme (1): CONCEPTS_INSEE\n  DataflowDefinition (1): IPI-2010-A21\n  DataStructureDefinition (1): IPI-2010-A21"

    @pytest.mark.parametrize(
        "pattern, expected", EXPECTED, ids=list(map(itemgetter(0), EXPECTED))
    )
    def test_message_repr(pattern, expected):
        with specimen(pattern) as f:
>           msg = sdmx.read_sdmx(f)
E           NameError: name 'sdmx' is not defined

pandasdmx\tests\test_message.py:81: NameError
_______________________ test_message_repr[dataflow.xml] _______________________

pattern = 'dataflow.xml'
expected = "<sdmx.StructureMessage>\n  <Header>\n    id: 'dataflow_ENQ-CONJ-TRES-IND-PERSP_1450865196042'\n    prepared: '2015-12...TRIM-ANC BPM6-CCAPITAL BPM6-CFINANCIER ...\n  DataStructureDefinition (663): ACT-TRIM-ANC BPM6-CCAPITAL BPM6-CFINAN..."

    @pytest.mark.parametrize(
        "pattern, expected", EXPECTED, ids=list(map(itemgetter(0), EXPECTED))
    )
    def test_message_repr(pattern, expected):
        with specimen(pattern) as f:
>           msg = sdmx.read_sdmx(f)
E           NameError: name 'sdmx' is not defined

pandasdmx\tests\test_message.py:81: NameError
________________________ test_message_repr[sg-xs.xml] _________________________

pattern = 'sg-xs.xml'
expected = "<sdmx.DataMessage>\n  <Header>\n    id: 'Generic'\n    prepared: '2010-01-04T16:21:49+01:00'\n    sender: <Agency ECB...st: False\n  DataSet (1)\n  dataflow: <DataflowDefinition (missing id)>\n  observation_dimension: <Dimension CURRENCY>"

    @pytest.mark.parametrize(
        "pattern, expected", EXPECTED, ids=list(map(itemgetter(0), EXPECTED))
    )
    def test_message_repr(pattern, expected):
        with specimen(pattern) as f:
>           msg = sdmx.read_sdmx(f)
E           NameError: name 'sdmx' is not defined

pandasdmx\tests\test_message.py:81: NameError
____________________ test_message_repr[action-delete.json] ____________________

pattern = 'action-delete.json'
expected = "<sdmx.DataMessage>\n  <Header>\n    id: '62b5f19d-f1c9-495d-8446-a3661ed24753'\n    prepared: '2012-11-29T08:40:26Z'\...: False\n  DataSet (2)\n  dataflow: <DataflowDefinition (missing id)>\n  observation_dimension: [<Dimension CURRENCY>]"

    @pytest.mark.parametrize(
        "pattern, expected", EXPECTED, ids=list(map(itemgetter(0), EXPECTED))
    )
    def test_message_repr(pattern, expected):
        with specimen(pattern) as f:
>           msg = sdmx.read_sdmx(f)
E           NameError: name 'sdmx' is not defined

pandasdmx\tests\test_message.py:81: NameError
__________________________ test_write_data_arguments __________________________

    def test_write_data_arguments():
        msg = pandasdmx.read_sdmx(test_files(kind="data")["argvalues"][0])
    
        # Attributes must be a string
        with raises(TypeError):
>           sdmx.to_pandas(msg, attributes=2)
E           NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:53: NameError
_________________________ test_write_dataset_datetime _________________________

    def test_write_dataset_datetime():
        """Test datetime arguments to write_dataset()."""
        # Load structure
        with specimen("IPI-2010-A21-structure.xml") as f:
            dsd = pandasdmx.read_sdmx(f).structure["IPI-2010-A21"]
            TIME_PERIOD = dsd.dimensions.get("TIME_PERIOD")
            FREQ = dsd.dimensions.get("FREQ")
    
        assert isinstance(TIME_PERIOD, TimeDimension)
    
        # Load data, two ways
        with specimen("IPI-2010-A21.xml") as f:
            msg = pandasdmx.read_sdmx(f, dsd=dsd)
            ds = msg.data[0]
        with specimen("IPI-2010-A21.xml") as f:
            msg_no_structure = pandasdmx.read_sdmx(f)
    
        other_dims = list(
            filter(lambda n: n != "TIME_PERIOD", [d.id for d in dsd.dimensions.components])
        )
    
        def expected(df, axis=0, cls=pd.DatetimeIndex):
            axes = ["index", "columns"] if axis else ["columns", "index"]
            assert getattr(df, axes[0]).names == other_dims
            assert isinstance(getattr(df, axes[1]), cls)
    
        # Write with datetime=str
        df = pandasdmx.to_pandas(ds, datetime="TIME_PERIOD")
        expected(df)
    
        # Write with datetime=Dimension instance
        df = pandasdmx.to_pandas(ds, datetime=TIME_PERIOD)
        expected(df)
    
        # Write with datetime=True fails because the data message contains no
        # actual structure information
        with pytest.raises(ValueError, match=r"no TimeDimension in \[.*\]"):
>           sdmx.to_pandas(msg_no_structure, datetime=True)
E           NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:231: NameError
---------------------------- Captured stderr call -----------------------------
2020-07-07 00:22:19,823 pandasdmx.reader.sdmxml - WARNING: Ambiguous: dsd=… argument for non–structure-specific message
------------------------------ Captured log call ------------------------------
WARNING  pandasdmx.reader.sdmxml:sdmxml.py:529 Ambiguous: dsd=… argument for non–structure-specific message
______________________ test_writer_structure[common.xml] ______________________

path = WindowsPath('C:/Users/a3305/documents/github/pandasdmx/pandasdmx/tests/data/ECB_EXR/common.xml')

    @pytest.mark.parametrize("path", **test_files(kind="structure"))
    def test_writer_structure(path):
        msg = pandasdmx.read_sdmx(path)
    
>       sdmx.to_pandas(msg)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:303: NameError
________________ test_writer_structure[ng-structure-full.xml] _________________

path = WindowsPath('C:/Users/a3305/documents/github/pandasdmx/pandasdmx/tests/data/ECB_EXR/ng-structure-full.xml')

    @pytest.mark.parametrize("path", **test_files(kind="structure"))
    def test_writer_structure(path):
        msg = pandasdmx.read_sdmx(path)
    
>       sdmx.to_pandas(msg)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:303: NameError
___________________ test_writer_structure[ng-structure.xml] ___________________

path = WindowsPath('C:/Users/a3305/documents/github/pandasdmx/pandasdmx/tests/data/ECB_EXR/ng-structure.xml')

    @pytest.mark.parametrize("path", **test_files(kind="structure"))
    def test_writer_structure(path):
        msg = pandasdmx.read_sdmx(path)
    
>       sdmx.to_pandas(msg)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:303: NameError
________________ test_writer_structure[rg-structure-full.xml] _________________

path = WindowsPath('C:/Users/a3305/documents/github/pandasdmx/pandasdmx/tests/data/ECB_EXR/rg-structure-full.xml')

    @pytest.mark.parametrize("path", **test_files(kind="structure"))
    def test_writer_structure(path):
        msg = pandasdmx.read_sdmx(path)
    
>       sdmx.to_pandas(msg)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:303: NameError
___________________ test_writer_structure[rg-structure.xml] ___________________

path = WindowsPath('C:/Users/a3305/documents/github/pandasdmx/pandasdmx/tests/data/ECB_EXR/rg-structure.xml')

    @pytest.mark.parametrize("path", **test_files(kind="structure"))
    def test_writer_structure(path):
        msg = pandasdmx.read_sdmx(path)
    
>       sdmx.to_pandas(msg)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:303: NameError
________________ test_writer_structure[sg-structure-full.xml] _________________

path = WindowsPath('C:/Users/a3305/documents/github/pandasdmx/pandasdmx/tests/data/ECB_EXR/sg-structure-full.xml')

    @pytest.mark.parametrize("path", **test_files(kind="structure"))
    def test_writer_structure(path):
        msg = pandasdmx.read_sdmx(path)
    
>       sdmx.to_pandas(msg)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:303: NameError
___________________ test_writer_structure[sg-structure.xml] ___________________

path = WindowsPath('C:/Users/a3305/documents/github/pandasdmx/pandasdmx/tests/data/ECB_EXR/sg-structure.xml')

    @pytest.mark.parametrize("path", **test_files(kind="structure"))
    def test_writer_structure(path):
        msg = pandasdmx.read_sdmx(path)
    
>       sdmx.to_pandas(msg)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:303: NameError
__________________ test_writer_structure[structure-full.xml] __________________

path = WindowsPath('C:/Users/a3305/documents/github/pandasdmx/pandasdmx/tests/data/ECB_EXR/1/structure-full.xml')

    @pytest.mark.parametrize("path", **test_files(kind="structure"))
    def test_writer_structure(path):
        msg = pandasdmx.read_sdmx(path)
    
>       sdmx.to_pandas(msg)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:303: NameError
____________________ test_writer_structure[structure.xml] _____________________

path = WindowsPath('C:/Users/a3305/documents/github/pandasdmx/pandasdmx/tests/data/ECB_EXR/1/structure.xml')

    @pytest.mark.parametrize("path", **test_files(kind="structure"))
    def test_writer_structure(path):
        msg = pandasdmx.read_sdmx(path)
    
>       sdmx.to_pandas(msg)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:303: NameError
---------------------------- Captured stderr call -----------------------------
2020-07-07 00:22:32,886 pandasdmx.model - INFO: [{'FREQ'}, set()]
------------------------------ Captured log call ------------------------------
INFO     pandasdmx.model:model.py:639 [{'FREQ'}, set()]
____________________ test_writer_structure[orgscheme.xml] _____________________

path = WindowsPath('C:/Users/a3305/documents/github/pandasdmx/pandasdmx/tests/data/ECB/orgscheme.xml')

    @pytest.mark.parametrize("path", **test_files(kind="structure"))
    def test_writer_structure(path):
        msg = pandasdmx.read_sdmx(path)
    
>       sdmx.to_pandas(msg)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:303: NameError
______________ test_writer_structure[apro_mk_cola-structure.xml] ______________

path = WindowsPath('C:/Users/a3305/documents/github/pandasdmx/pandasdmx/tests/data/ESTAT/apro_mk_cola-structure.xml')

    @pytest.mark.parametrize("path", **test_files(kind="structure"))
    def test_writer_structure(path):
        msg = pandasdmx.read_sdmx(path)
    
>       sdmx.to_pandas(msg)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:303: NameError
_______________ test_writer_structure[ECOFIN_DSD-structure.xml] _______________

path = WindowsPath('C:/Users/a3305/documents/github/pandasdmx/pandasdmx/tests/data/IMF/ECOFIN_DSD-structure.xml')

    @pytest.mark.parametrize("path", **test_files(kind="structure"))
    def test_writer_structure(path):
        msg = pandasdmx.read_sdmx(path)
    
>       sdmx.to_pandas(msg)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:303: NameError
---------------------------- Captured stderr call -----------------------------
2020-07-07 00:22:33,434 pandasdmx.reader.sdmxml - WARNING: None has no Dimension with ID REF_AREA; XML element ignored and MemberValues discarded
2020-07-07 00:22:33,434 pandasdmx.model - INFO: [{'US3'}, set()]
------------------------------ Captured log call ------------------------------
WARNING  pandasdmx.reader.sdmxml:sdmxml.py:1023 None has no Dimension with ID REF_AREA; XML element ignored and MemberValues discarded
INFO     pandasdmx.model:model.py:639 [{'US3'}, set()]
_________ test_writer_structure[CNA-2010-CONSO-SI-A17-structure.xml] __________

path = WindowsPath('C:/Users/a3305/documents/github/pandasdmx/pandasdmx/tests/data/INSEE/CNA-2010-CONSO-SI-A17-structure.xml')

    @pytest.mark.parametrize("path", **test_files(kind="structure"))
    def test_writer_structure(path):
        msg = pandasdmx.read_sdmx(path)
    
>       sdmx.to_pandas(msg)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:303: NameError
_____________________ test_writer_structure[dataflow.xml] _____________________

path = WindowsPath('C:/Users/a3305/documents/github/pandasdmx/pandasdmx/tests/data/INSEE/dataflow.xml')

    @pytest.mark.parametrize("path", **test_files(kind="structure"))
    def test_writer_structure(path):
        msg = pandasdmx.read_sdmx(path)
    
>       sdmx.to_pandas(msg)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:303: NameError
______________ test_writer_structure[IPI-2010-A21-structure.xml] ______________

path = WindowsPath('C:/Users/a3305/documents/github/pandasdmx/pandasdmx/tests/data/INSEE/IPI-2010-A21-structure.xml')

    @pytest.mark.parametrize("path", **test_files(kind="structure"))
    def test_writer_structure(path):
        msg = pandasdmx.read_sdmx(path)
    
>       sdmx.to_pandas(msg)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:303: NameError
_________________ test_writer_structure[47_850-structure.xml] _________________

path = WindowsPath('C:/Users/a3305/documents/github/pandasdmx/pandasdmx/tests/data/ISTAT/47_850-structure.xml')

    @pytest.mark.parametrize("path", **test_files(kind="structure"))
    def test_writer_structure(path):
        msg = pandasdmx.read_sdmx(path)
    
>       pandasdmx.to_pandas(msg)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:303: NameError
_________________ test_writer_structure[codelist_partial.xml] _________________

path = WindowsPath('C:/Users/a3305/documents/github/pandasdmx/pandasdmx/tests/data/UNSD/codelist_partial.xml')

    @pytest.mark.parametrize("path", **test_files(kind="structure"))
    def test_writer_structure(path):
        msg = pandasdmx.read_sdmx(path)
    
>       pandasdmx.to_pandas(msg)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:303: NameError
_________________ test_writer_structure[common-structure.xml] _________________

path = WindowsPath('C:/Users/a3305/documents/github/pandasdmx/pandasdmx/tests/data/SGR/common-structure.xml')

    @pytest.mark.parametrize("path", **test_files(kind="structure"))
    def test_writer_structure(path):
        msg = pandasdmx.read_sdmx(path)
    
>       pandasdmx.to_pandas(msg)
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_pandas.py:303: NameError
________________________________ test_codelist ________________________________

tmp_path = WindowsPath('C:/Users/a3305/AppData/Local/Temp/pytest-of-a3305/pytest-4/test_codelist0')
codelist = <Codelist ECB:CL_COLLECTION(1.0) (3 items): Collection indicator code list>

    def test_codelist(tmp_path, codelist):
>       result = pandasdmx.to_xml(codelist, pretty_print=True)

pandasdmx\tests\writer\test_writer_xml.py:13: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
pandasdmx\writer\xml.py:46: in to_xml
    return etree.tostring(writer.recurse(obj), **kwargs)
pandasdmx\writer\base.py:53: in recurse
    return dispatcher(obj, *args, **kwargs)
..\..\..\Anaconda3\envs\sdmx37\lib\functools.py:840: in wrapper
    return dispatch(args[0].__class__)(*args, **kw)
pandasdmx\writer\xml.py:239: in _is
    elem = maintainable(obj)
pandasdmx\writer\xml.py:218: in maintainable
    return nameable(obj, **kwargs)
pandasdmx\writer\xml.py:207: in nameable
    elem = identifiable(obj, **kwargs)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

obj = <Codelist ECB:CL_COLLECTION(1.0) (3 items): Collection indicator code list>
kwargs = {'agencyID': 'ECB', 'id': 'CL_COLLECTION', 'isExternalReference': 'false', 'isFinal': 'false', ...}

    def identifiable(obj, **kwargs):
        kwargs.setdefault("id", obj.id)
        try:
            kwargs.setdefault(
>               "urn", obj.urn or sdmx.urn.make(obj, kwargs.pop("parent", None))
            )
E           NameError: name 'sdmx' is not defined

pandasdmx\writer\xml.py:199: NameError
____________________________ test_structuremessage ____________________________

tmp_path = WindowsPath('C:/Users/a3305/AppData/Local/Temp/pytest-of-a3305/pytest-4/test_structuremessage0')
structuremessage = <pandasdmx.StructureMessage>
  <Header>
    source: 
    test: False
  Codelist (1): CL_COLLECTION

    def test_structuremessage(tmp_path, structuremessage):
>       result = pandasdmx.to_xml(structuremessage, pretty_print=True)

pandasdmx\tests\writer\test_writer_xml.py:18: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
pandasdmx\writer\xml.py:46: in to_xml
    return etree.tostring(writer.recurse(obj), **kwargs)
pandasdmx\writer\base.py:53: in recurse
    return dispatcher(obj, *args, **kwargs)
..\..\..\Anaconda3\envs\sdmx37\lib\functools.py:840: in wrapper
    return dispatch(args[0].__class__)(*args, **kw)
pandasdmx\writer\xml.py:128: in _sm
    container.extend(writer.recurse(s) for s in getattr(obj, attr).values())
src/lxml/etree.pyx:871: in lxml.etree._Element.extend
    ???
pandasdmx\writer\xml.py:128: in <genexpr>
    container.extend(writer.recurse(s) for s in getattr(obj, attr).values())
pandasdmx\writer\base.py:53: in recurse
    return dispatcher(obj, *args, **kwargs)
..\..\..\Anaconda3\envs\sdmx37\lib\functools.py:840: in wrapper
    return dispatch(args[0].__class__)(*args, **kw)
pandasdmx\writer\xml.py:239: in _is
    elem = maintainable(obj)
pandasdmx\writer\xml.py:218: in maintainable
    return nameable(obj, **kwargs)
pandasdmx\writer\xml.py:207: in nameable
    elem = identifiable(obj, **kwargs)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

obj = <Codelist ECB:CL_COLLECTION(1.0) (3 items): Collection indicator code list>
kwargs = {'agencyID': 'ECB', 'id': 'CL_COLLECTION', 'isExternalReference': 'false', 'isFinal': 'false', ...}

    def identifiable(obj, **kwargs):
        kwargs.setdefault("id", obj.id)
        try:
            kwargs.setdefault(
>               "urn", obj.urn or sdmx.urn.make(obj, kwargs.pop("parent", None))
            )
E           NameError: name 'sdmx' is not defined

pandasdmx\writer\xml.py:199: NameError
______________ test_structure_roundtrip[ECB/orgscheme.xml-True] _______________

pytestconfig = <_pytest.config.Config object at 0x000001DEF4459E88>
specimen_id = 'ECB/orgscheme.xml', strict = True
tmp_path = WindowsPath('C:/Users/a3305/AppData/Local/Temp/pytest-of-a3305/pytest-4/test_structure_roundtrip_ECB_o0')

    @pytest.mark.parametrize(
        "specimen_id, strict",
        [
            ("ECB/orgscheme.xml", True),
            ("ECB_EXR/1/structure-full.xml", False),
            ("ESTAT/apro_mk_cola-structure.xml", True),
            pytest.param(
                "ISTAT/47_850-structure.xml", True, marks=[pytest.mark.skip(reason="Slow")],
            ),
            pytest.param("IMF/ECOFIN_DSD-structure.xml", True, marks=_xf_ref),
            ("INSEE/CNA-2010-CONSO-SI-A17-structure.xml", False),
            ("INSEE/IPI-2010-A21-structure.xml", False),
            pytest.param("INSEE/dataflow.xml", False, marks=_xf_not_equal),
            ("SGR/common-structure.xml", True),
            ("UNSD/codelist_partial.xml", True),
        ],
    )
    def test_structure_roundtrip(pytestconfig, specimen_id, strict, tmp_path):
        """Test that pandasdmx.ML StructureMessages can be 'round-tripped'."""
    
        # Read a specimen file
        with specimen(specimen_id) as f:
            msg0 = pandasdmx.read_sdmx(f)
    
        # Write to file
        path = tmp_path / "output.xml"
>       path.write_bytes(sdmx.to_xml(msg0, pretty_print=True))
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_writer_xml.py:71: NameError
________ test_structure_roundtrip[ECB_EXR/1/structure-full.xml-False] _________

pytestconfig = <_pytest.config.Config object at 0x000001DEF4459E88>
specimen_id = 'ECB_EXR/1/structure-full.xml', strict = False
tmp_path = WindowsPath('C:/Users/a3305/AppData/Local/Temp/pytest-of-a3305/pytest-4/test_structure_roundtrip_ECB_E0')

    @pytest.mark.parametrize(
        "specimen_id, strict",
        [
            ("ECB/orgscheme.xml", True),
            ("ECB_EXR/1/structure-full.xml", False),
            ("ESTAT/apro_mk_cola-structure.xml", True),
            pytest.param(
                "ISTAT/47_850-structure.xml", True, marks=[pytest.mark.skip(reason="Slow")],
            ),
            pytest.param("IMF/ECOFIN_DSD-structure.xml", True, marks=_xf_ref),
            ("INSEE/CNA-2010-CONSO-SI-A17-structure.xml", False),
            ("INSEE/IPI-2010-A21-structure.xml", False),
            pytest.param("INSEE/dataflow.xml", False, marks=_xf_not_equal),
            ("SGR/common-structure.xml", True),
            ("UNSD/codelist_partial.xml", True),
        ],
    )
    def test_structure_roundtrip(pytestconfig, specimen_id, strict, tmp_path):
        """Test that pandasdmx.ML StructureMessages can be 'round-tripped'."""
    
        # Read a specimen file
        with specimen(specimen_id) as f:
            msg0 = pandasdmx.read_sdmx(f)
    
        # Write to file
        path = tmp_path / "output.xml"
>       path.write_bytes(sdmx.to_xml(msg0, pretty_print=True))
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_writer_xml.py:71: NameError
_______ test_structure_roundtrip[ESTAT/apro_mk_cola-structure.xml-True] _______

pytestconfig = <_pytest.config.Config object at 0x000001DEF4459E88>
specimen_id = 'ESTAT/apro_mk_cola-structure.xml', strict = True
tmp_path = WindowsPath('C:/Users/a3305/AppData/Local/Temp/pytest-of-a3305/pytest-4/test_structure_roundtrip_ESTAT0')

    @pytest.mark.parametrize(
        "specimen_id, strict",
        [
            ("ECB/orgscheme.xml", True),
            ("ECB_EXR/1/structure-full.xml", False),
            ("ESTAT/apro_mk_cola-structure.xml", True),
            pytest.param(
                "ISTAT/47_850-structure.xml", True, marks=[pytest.mark.skip(reason="Slow")],
            ),
            pytest.param("IMF/ECOFIN_DSD-structure.xml", True, marks=_xf_ref),
            ("INSEE/CNA-2010-CONSO-SI-A17-structure.xml", False),
            ("INSEE/IPI-2010-A21-structure.xml", False),
            pytest.param("INSEE/dataflow.xml", False, marks=_xf_not_equal),
            ("SGR/common-structure.xml", True),
            ("UNSD/codelist_partial.xml", True),
        ],
    )
    def test_structure_roundtrip(pytestconfig, specimen_id, strict, tmp_path):
        """Test that pandasdmx.ML StructureMessages can be 'round-tripped'."""
    
        # Read a specimen file
        with specimen(specimen_id) as f:
            msg0 = pandasdmx.read_sdmx(f)
    
        # Write to file
        path = tmp_path / "output.xml"
>       path.write_bytes(sdmx.to_xml(msg0, pretty_print=True))
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_writer_xml.py:71: NameError
_________ test_structure_roundtrip[IMF/ECOFIN_DSD-structure.xml-True] _________

pytestconfig = <_pytest.config.Config object at 0x000001DEF4459E88>
specimen_id = 'IMF/ECOFIN_DSD-structure.xml', strict = True
tmp_path = WindowsPath('C:/Users/a3305/AppData/Local/Temp/pytest-of-a3305/pytest-4/test_structure_roundtrip_IMF_E0')

    @pytest.mark.parametrize(
        "specimen_id, strict",
        [
            ("ECB/orgscheme.xml", True),
            ("ECB_EXR/1/structure-full.xml", False),
            ("ESTAT/apro_mk_cola-structure.xml", True),
            pytest.param(
                "ISTAT/47_850-structure.xml", True, marks=[pytest.mark.skip(reason="Slow")],
            ),
            pytest.param("IMF/ECOFIN_DSD-structure.xml", True, marks=_xf_ref),
            ("INSEE/CNA-2010-CONSO-SI-A17-structure.xml", False),
            ("INSEE/IPI-2010-A21-structure.xml", False),
            pytest.param("INSEE/dataflow.xml", False, marks=_xf_not_equal),
            ("SGR/common-structure.xml", True),
            ("UNSD/codelist_partial.xml", True),
        ],
    )
    def test_structure_roundtrip(pytestconfig, specimen_id, strict, tmp_path):
        """Test that pandasdmx.ML StructureMessages can be 'round-tripped'."""
    
        # Read a specimen file
        with specimen(specimen_id) as f:
            msg0 = pandasdmx.read_sdmx(f)
    
        # Write to file
        path = tmp_path / "output.xml"
>       path.write_bytes(sdmx.to_xml(msg0, pretty_print=True))
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_writer_xml.py:71: NameError
---------------------------- Captured stderr call -----------------------------
2020-07-07 00:23:46,449 pandasdmx.reader.sdmxml - WARNING: None has no Dimension with ID REF_AREA; XML element ignored and MemberValues discarded
2020-07-07 00:23:46,449 pandasdmx.model - INFO: [{'US3'}, set()]
------------------------------ Captured log call ------------------------------
WARNING  pandasdmx.reader.sdmxml:sdmxml.py:1023 None has no Dimension with ID REF_AREA; XML element ignored and MemberValues discarded
INFO     pandasdmx.model:model.py:639 [{'US3'}, set()]
__ test_structure_roundtrip[INSEE/CNA-2010-CONSO-SI-A17-structure.xml-False] __

pytestconfig = <_pytest.config.Config object at 0x000001DEF4459E88>
specimen_id = 'INSEE/CNA-2010-CONSO-SI-A17-structure.xml', strict = False
tmp_path = WindowsPath('C:/Users/a3305/AppData/Local/Temp/pytest-of-a3305/pytest-4/test_structure_roundtrip_INSEE0')

    @pytest.mark.parametrize(
        "specimen_id, strict",
        [
            ("ECB/orgscheme.xml", True),
            ("ECB_EXR/1/structure-full.xml", False),
            ("ESTAT/apro_mk_cola-structure.xml", True),
            pytest.param(
                "ISTAT/47_850-structure.xml", True, marks=[pytest.mark.skip(reason="Slow")],
            ),
            pytest.param("IMF/ECOFIN_DSD-structure.xml", True, marks=_xf_ref),
            ("INSEE/CNA-2010-CONSO-SI-A17-structure.xml", False),
            ("INSEE/IPI-2010-A21-structure.xml", False),
            pytest.param("INSEE/dataflow.xml", False, marks=_xf_not_equal),
            ("SGR/common-structure.xml", True),
            ("UNSD/codelist_partial.xml", True),
        ],
    )
    def test_structure_roundtrip(pytestconfig, specimen_id, strict, tmp_path):
        """Test that pandasdmx.ML StructureMessages can be 'round-tripped'."""
    
        # Read a specimen file
        with specimen(specimen_id) as f:
            msg0 = pandasdmx.read_sdmx(f)
    
        # Write to file
        path = tmp_path / "output.xml"
>       path.write_bytes(sdmx.to_xml(msg0, pretty_print=True))
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_writer_xml.py:71: NameError
______ test_structure_roundtrip[INSEE/IPI-2010-A21-structure.xml-False] _______

pytestconfig = <_pytest.config.Config object at 0x000001DEF4459E88>
specimen_id = 'INSEE/IPI-2010-A21-structure.xml', strict = False
tmp_path = WindowsPath('C:/Users/a3305/AppData/Local/Temp/pytest-of-a3305/pytest-4/test_structure_roundtrip_INSEE1')

    @pytest.mark.parametrize(
        "specimen_id, strict",
        [
            ("ECB/orgscheme.xml", True),
            ("ECB_EXR/1/structure-full.xml", False),
            ("ESTAT/apro_mk_cola-structure.xml", True),
            pytest.param(
                "ISTAT/47_850-structure.xml", True, marks=[pytest.mark.skip(reason="Slow")],
            ),
            pytest.param("IMF/ECOFIN_DSD-structure.xml", True, marks=_xf_ref),
            ("INSEE/CNA-2010-CONSO-SI-A17-structure.xml", False),
            ("INSEE/IPI-2010-A21-structure.xml", False),
            pytest.param("INSEE/dataflow.xml", False, marks=_xf_not_equal),
            ("SGR/common-structure.xml", True),
            ("UNSD/codelist_partial.xml", True),
        ],
    )
    def test_structure_roundtrip(pytestconfig, specimen_id, strict, tmp_path):
        """Test that pandasdmx.ML StructureMessages can be 'round-tripped'."""
    
        # Read a specimen file
        with specimen(specimen_id) as f:
            msg0 = pandasdmx.read_sdmx(f)
    
        # Write to file
        path = tmp_path / "output.xml"
>       path.write_bytes(sdmx.to_xml(msg0, pretty_print=True))
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_writer_xml.py:71: NameError
_____________ test_structure_roundtrip[INSEE/dataflow.xml-False] ______________

pytestconfig = <_pytest.config.Config object at 0x000001DEF4459E88>
specimen_id = 'INSEE/dataflow.xml', strict = False
tmp_path = WindowsPath('C:/Users/a3305/AppData/Local/Temp/pytest-of-a3305/pytest-4/test_structure_roundtrip_INSEE2')

    @pytest.mark.parametrize(
        "specimen_id, strict",
        [
            ("ECB/orgscheme.xml", True),
            ("ECB_EXR/1/structure-full.xml", False),
            ("ESTAT/apro_mk_cola-structure.xml", True),
            pytest.param(
                "ISTAT/47_850-structure.xml", True, marks=[pytest.mark.skip(reason="Slow")],
            ),
            pytest.param("IMF/ECOFIN_DSD-structure.xml", True, marks=_xf_ref),
            ("INSEE/CNA-2010-CONSO-SI-A17-structure.xml", False),
            ("INSEE/IPI-2010-A21-structure.xml", False),
            pytest.param("INSEE/dataflow.xml", False, marks=_xf_not_equal),
            ("SGR/common-structure.xml", True),
            ("UNSD/codelist_partial.xml", True),
        ],
    )
    def test_structure_roundtrip(pytestconfig, specimen_id, strict, tmp_path):
        """Test that pandasdmx.ML StructureMessages can be 'round-tripped'."""
    
        # Read a specimen file
        with specimen(specimen_id) as f:
            msg0 = pandasdmx.read_sdmx(f)
    
        # Write to file
        path = tmp_path / "output.xml"
>       path.write_bytes(sdmx.to_xml(msg0, pretty_print=True))
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_writer_xml.py:71: NameError
___________ test_structure_roundtrip[SGR/common-structure.xml-True] ___________

pytestconfig = <_pytest.config.Config object at 0x000001DEF4459E88>
specimen_id = 'SGR/common-structure.xml', strict = True
tmp_path = WindowsPath('C:/Users/a3305/AppData/Local/Temp/pytest-of-a3305/pytest-4/test_structure_roundtrip_SGR_c0')

    @pytest.mark.parametrize(
        "specimen_id, strict",
        [
            ("ECB/orgscheme.xml", True),
            ("ECB_EXR/1/structure-full.xml", False),
            ("ESTAT/apro_mk_cola-structure.xml", True),
            pytest.param(
                "ISTAT/47_850-structure.xml", True, marks=[pytest.mark.skip(reason="Slow")],
            ),
            pytest.param("IMF/ECOFIN_DSD-structure.xml", True, marks=_xf_ref),
            ("INSEE/CNA-2010-CONSO-SI-A17-structure.xml", False),
            ("INSEE/IPI-2010-A21-structure.xml", False),
            pytest.param("INSEE/dataflow.xml", False, marks=_xf_not_equal),
            ("SGR/common-structure.xml", True),
            ("UNSD/codelist_partial.xml", True),
        ],
    )
    def test_structure_roundtrip(pytestconfig, specimen_id, strict, tmp_path):
        """Test that pandasdmx.ML StructureMessages can be 'round-tripped'."""
    
        # Read a specimen file
        with specimen(specimen_id) as f:
            msg0 = pandasdmx.read_sdmx(f)
    
        # Write to file
        path = tmp_path / "output.xml"
>       path.write_bytes(sdmx.to_xml(msg0, pretty_print=True))
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_writer_xml.py:71: NameError
__________ test_structure_roundtrip[UNSD/codelist_partial.xml-True] ___________

pytestconfig = <_pytest.config.Config object at 0x000001DEF4459E88>
specimen_id = 'UNSD/codelist_partial.xml', strict = True
tmp_path = WindowsPath('C:/Users/a3305/AppData/Local/Temp/pytest-of-a3305/pytest-4/test_structure_roundtrip_UNSD_0')

    @pytest.mark.parametrize(
        "specimen_id, strict",
        [
            ("ECB/orgscheme.xml", True),
            ("ECB_EXR/1/structure-full.xml", False),
            ("ESTAT/apro_mk_cola-structure.xml", True),
            pytest.param(
                "ISTAT/47_850-structure.xml", True, marks=[pytest.mark.skip(reason="Slow")],
            ),
            pytest.param("IMF/ECOFIN_DSD-structure.xml", True, marks=_xf_ref),
            ("INSEE/CNA-2010-CONSO-SI-A17-structure.xml", False),
            ("INSEE/IPI-2010-A21-structure.xml", False),
            pytest.param("INSEE/dataflow.xml", False, marks=_xf_not_equal),
            ("SGR/common-structure.xml", True),
            ("UNSD/codelist_partial.xml", True),
        ],
    )
    def test_structure_roundtrip(pytestconfig, specimen_id, strict, tmp_path):
        """Test that pandasdmx.ML StructureMessages can be 'round-tripped'."""
    
        # Read a specimen file
        with specimen(specimen_id) as f:
            msg0 = pandasdmx.read_sdmx(f)
    
        # Write to file
        path = tmp_path / "output.xml"
>       path.write_bytes(sdmx.to_xml(msg0, pretty_print=True))
E       NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_writer_xml.py:71: NameError
____________________________ test_not_implemented _____________________________

    def test_not_implemented():
        msg = DataMessage()
    
        with pytest.raises(NotImplementedError, match="write DataMessage to XML"):
>           pandasdmx.to_xml(msg)
E           NameError: name 'sdmx' is not defined

pandasdmx\tests\writer\test_writer_xml.py:86: NameError


= 53 failed, 166 passed, 2 skipped, 82 deselected, 1 xfailed, 25 errors in 208.23s (0:03:28) =

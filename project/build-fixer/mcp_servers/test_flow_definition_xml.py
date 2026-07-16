from jenkins_status import _flow_definition_xml


def test_embeds_script_and_structure():
    xml = _flow_definition_xml("pipeline { agent any }")
    assert xml.lstrip().startswith("<?xml")
    assert "<flow-definition" in xml
    assert "CpsFlowDefinition" in xml
    assert "<sandbox>true</sandbox>" in xml
    assert "pipeline { agent any }" in xml


def test_escapes_xml_special_chars():
    xml = _flow_definition_xml("echo '<a> & <b>'")
    # The angle brackets from the script must be escaped so the XML stays valid.
    assert "<a>" not in xml.replace("<flow-definition", "").replace("<definition", "")
    assert "&lt;a&gt;" in xml
    assert "&amp;" in xml

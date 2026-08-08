"""Auto-generated MCP wrapper for safe_text_smoke
"""
import tempfile
import json
import os
from core.powershell import run_powershell

SCRIPT_CONTENT = r"""Write-Output 'Auto-generated fix for: screen brightness'
Write-Output 'LLM says: Screenbrightnessreferstotheintensityoflightemittedbythedisplayscreenofanelectronicdevice
,
suchasacomputermonitor
,
smartphone
,
ortablet
.
Adjustingthescreenbrightnesscanhelpreduceeyestrainandsaveenergy
.
Herearesomegeneraltipsforadjustingscreenbrightness
:
1
.
**
AutomateBrightnessAdjustment
**:
Manydevicesallowyoutosetautomaticbrightnessadjustmentbasedonambientlightlevels
.
Thiscanbefoundinthedevice
''ssettingsunderdisplayorscreenoptions
.
2
.
**
ManualAdjustment
**:
Mostdeviceshaveadedicatedbuttonorsliderwithinthedisplaysettingstomanuallyincreaseordecreasethebrightnesslevel
.
3
.
**
LowLightMode
**:
Somedeviceshavealowlightmodethatautomaticallyreducesthebrightnesswhenambientlightlevelsarelow
,
suchasinadarkroom
.
4
.
**
SaveBatteryLife
**:
Reducingscreenbrightnesscanalsohelpextendbatterylifeonmobiledevices
.
5
.
**
Consistency
**:
It
''sagoodpracticetokeepthescreenbrightnessconsistentacrossdifferentenvironmentsandsituationstoavoideyestrain
.
Rememberthattheoptimalbrightnesslevelcanvaryfrompersontopersonbasedonindividualsensitivitytolight
.'
"""


def run():
    # write script to temp file and execute via PowerShell wrapper
    fd, path = tempfile.mkstemp(suffix=".ps1")
    os.close(fd)
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write(SCRIPT_CONTENT)
    res = run_powershell("& '" + path.replace("'", "''") + "'")
    # cleanup
    try:
        os.remove(path)
    except Exception:
        pass
    return res


if __name__ == "__main__":
    print(json.dumps(run()))

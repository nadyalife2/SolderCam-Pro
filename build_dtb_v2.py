import fdt

with open(r"d:\для one plus nord n10\dtbo_extracted\entry_01.dtb", "rb") as f:
    tree = fdt.parse_dtb(f.read())

print("Original tree loaded.")

# 1. fragment@126
frag126 = tree.get_node("fragment@126")
overlay126 = frag126.get_subnode("__overlay__")

# set 100 kHz clock for I2C standard mode
overlay126.set_property("qcom,clk-freq-out", 100000)
overlay126.set_property("clock-frequency", 100000)

# remove qcom,enable-ocp-broadcast from pm8008-regulator
pm8008_9 = overlay126.get_subnode("qcom,pm8008@9")
regulator = pm8008_9.get_subnode("qcom,pm8008-regulator")
if regulator.get_property("qcom,enable-ocp-broadcast"):
    regulator.remove_property("qcom,enable-ocp-broadcast")
    print("Removed qcom,enable-ocp-broadcast")

# 2. Add fragment@134 for pm8150a_l1 (cam_vio always-on and boot-on)
frag134 = fdt.Node("fragment@134")
frag134.set_property("target", 0xFFFFFFFF)
overlay134 = fdt.Node("__overlay__")
overlay134.set_property("regulator-always-on", None)
overlay134.set_property("regulator-boot-on", None)
frag134.append(overlay134)
tree.root.append(frag134)
print("Added fragment@134 for pm8150a_l1")

# Update __fixups__
fixups = tree.get_node("__fixups__")
pm8150a_l1_prop = fixups.get_property("pm8150a_l1")
new_val = list(pm8150a_l1_prop.data)
new_val.append("/fragment@134:target:0")
fixups.set_property("pm8150a_l1", new_val)
print("Updated __fixups__ for pm8150a_l1")

# Serialize back to DTB
dtb_data = tree.to_dtb()
out_path = r"d:\для one plus nord n10\dtbo_extracted\entry_01_mod_v2.dtb"
with open(out_path, "wb") as f:
    f.write(dtb_data)

print(f"Saved {out_path}, size={len(dtb_data)} bytes")

set run_dir      $::env(RUN_DIR)
set design       $::env(DESIGN_NAME)
set corner       $::env(CORNER)
set pdk_dir      $::env(PDK_DIR)
set vcd_file     $::env(VCD_FILE)
set vcd_scope    $::env(VCD_SCOPE)
set clock_period $::env(CLOCK_PERIOD)

read_liberty $pdk_dir/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_typ_1p20V_25C.lib
read_verilog $run_dir/final/nl/$design.nl.v
link_design $design

read_sdf $run_dir/final/sdf/$corner/${design}__${corner}.sdf
read_spef $run_dir/final/spef/nom/$design.nom.spef

create_clock -name clk_i -period $clock_period [get_ports clk_i]
set_propagated_clock [all_clocks]

puts "\n=== reading switching activity from $vcd_file ==="
read_vcd -scope $vcd_scope $vcd_file
report_activity_annotation

puts "\n=== power over the operating window only ==="
report_power

exit

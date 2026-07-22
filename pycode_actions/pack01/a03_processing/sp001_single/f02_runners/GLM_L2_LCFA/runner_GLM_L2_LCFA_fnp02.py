"""
Path:
legion_goes/pycode_actions/pack01/a03_processing/sp001_single/f02_runners/GLM_L2_LCFA/runner_GLM_L2_LCFA_fnp02.py

Description:
    Runner for GLM-L2-LCFA FNP02.

    This runner creates one GLM electrical-storm frame anchored to one
    ABI-L2-MCMIPF scan. It writes outputs below data_proc using the same broad
    folder structure used by the other single-product processors.
"""

# ==============================================================================================================================================
# Execution example:
# python -m legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f02_runners.GLM_L2_LCFA.runner_GLM_L2_LCFA_fnp02
# ==============================================================================================================================================

from pathlib import Path

from legion_goes.pycode_actions.pack01.a03_processing.sp001_single.f01_code.GLM_L2_LCFA.proc_GLM_L2_LCFA_fnp02 import (
    gen_dict_output_file_name,
    get_required_output_keys,
    parse_goes_filename,
    run_proc_GLM_L2_LCFA_fnp02,
)


def gen_str_folder_output(mcmipf_nc_path):
    """
    Generates the relative output folder for one MCMIPF-anchored GLM frame.
    """

    info = parse_goes_filename(mcmipf_nc_path)

    if info["product"] != "ABI-L2-MCMIPF":
        raise ValueError("The GLM FNP02 runner must be anchored to ABI-L2-MCMIPF.")

    return (
        Path("sp01_single")
        / f"noaa-goes{info['sat_number']}-{info['position']}"
        / "GLM-L2-LCFA"
        / info["start_raw"][0:4]
        / info["start_raw"][4:7]
        / info["start_raw"][7:9]
        / f"s{info['start_raw']}"
        / "GLM-L2-LCFA_fnp02"
    )


def gen_dict_path_output(mcmipf_nc_path, str_folder_path_data_proc=None):
    """
    Creates the output directory and returns full output paths.
    """

    if str_folder_path_data_proc is None:
        data_proc_dir = Path.cwd() / "data_proc"
    else:
        data_proc_dir = Path(str_folder_path_data_proc).expanduser().resolve()

    if data_proc_dir.exists() and not data_proc_dir.is_dir():
        raise ValueError(f"data_proc path exists but is not a folder: {data_proc_dir}")

    data_proc_dir.mkdir(parents=True, exist_ok=True)

    output_folder = data_proc_dir / gen_str_folder_output(mcmipf_nc_path)
    output_folder.mkdir(parents=True, exist_ok=True)

    file_names = gen_dict_output_file_name(mcmipf_nc_path)

    return {
        key: output_folder / file_name
        for key, file_name in file_names.items()
    }


def is_processing_complete(output_dict):
    """
    Returns True only when every mandatory output exists and is non-empty.
    """

    for key in get_required_output_keys():
        path = Path(output_dict[key])

        if not path.exists() or not path.is_file() or path.stat().st_size == 0:
            return False

    return True


def run_runner_GLM_L2_LCFA_fnp02(
    mcmipf_nc_path,
    glm_nc_paths,
    str_folder_path_data_proc=None,
    overwrite=False,
    matching_mode="overlap",
    quality_good_only=True,
    width=3600,
    height=1800,
    point_radius_px=7,
    density_lon_step=1.0,
    density_lat_step=1.0,
    heatmap_blur_radius_px=14,
):
    """
    Runs GLM FNP02 and manages output paths, skip logic, and cleanup.
    """

    mcmipf_nc_path = Path(mcmipf_nc_path)
    glm_nc_paths = [Path(path) for path in glm_nc_paths]
    output_paths = gen_dict_path_output(
        mcmipf_nc_path=mcmipf_nc_path,
        str_folder_path_data_proc=str_folder_path_data_proc,
    )

    if is_processing_complete(output_paths) and not overwrite:
        print(
            f"  [SKIPPED]     {mcmipf_nc_path.name} "
            f"(All {len(get_required_output_keys())} GLM FNP02 outputs exist)"
        )
        return True

    exists_count = sum(
        1
        for key in get_required_output_keys()
        if output_paths[key].exists() and output_paths[key].stat().st_size > 0
    )

    if overwrite:
        reason = "OVERWRITE"
    elif exists_count > 0:
        reason = f"INCOMPLETE ({exists_count}/{len(get_required_output_keys())})"
    else:
        reason = "NEW"

    print(f"  [PROCESSING]  {mcmipf_nc_path.name}")
    print(f"                Reason: {reason}")
    print(f"                GLM candidates: {len(glm_nc_paths)}")

    for path in output_paths.values():
        if path.exists():
            path.unlink()

    output_kwargs = {key: str(path) for key, path in output_paths.items()}

    success = run_proc_GLM_L2_LCFA_fnp02(
        mcmipf_nc_path=str(mcmipf_nc_path),
        glm_nc_paths=[str(path) for path in glm_nc_paths],
        matching_mode=matching_mode,
        quality_good_only=quality_good_only,
        width=width,
        height=height,
        point_radius_px=point_radius_px,
        density_lon_step=density_lon_step,
        density_lat_step=density_lat_step,
        heatmap_blur_radius_px=heatmap_blur_radius_px,
        **output_kwargs,
    )

    if not success:
        return False

    return is_processing_complete(output_paths)


if __name__ == "__main__":
    print("\n" + " Runner GLM-L2-LCFA FNP02 DIAGNOSTIC ".center(80, "="))

    current_dir = Path.cwd()
    mcmipf_candidates = sorted(current_dir.rglob("*ABI-L2-MCMIPF*.nc"))
    glm_candidates = sorted(current_dir.rglob("*GLM-L2-LCFA*.nc"))

    if not mcmipf_candidates:
        print(f"No MCMIPF NetCDF files found under: {current_dir}")
    elif not glm_candidates:
        print(f"No GLM NetCDF files found under: {current_dir}")
    else:
        ok = run_runner_GLM_L2_LCFA_fnp02(
            mcmipf_nc_path=mcmipf_candidates[0],
            glm_nc_paths=glm_candidates,
            str_folder_path_data_proc=current_dir / "data_proc",
            overwrite=True,
        )
        print(f"Diagnostic result: {ok}")

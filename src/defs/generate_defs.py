""" Generate dataclasses and enums from JSON files and create a master file. """

from pathlib import Path
from datamodel_code_generator import InputFileType, generate


def generate_dataclasses_from_json(input_json: str, output_file: str) -> None:
    """
    Generate dataclasses and enums from a JSON file and save to the specified output file.

    Args:
        input_json (str): Path to the input JSON file.
        output_file (str): Path to the output Python file.
    """
    input_path = Path(input_json)
    output_path = Path(output_file)

    generate(
        input_=input_path.read_text(encoding="utf-8"),
        input_file_type=InputFileType.Json,
        output=output_path,
    )
    print(f"Generated dataclasses and enums from {input_json}.")


def generate_definitions_and_master(
    input_folder: str, output_dir: str, master_file_path: str
) -> None:
    """
    Generate dataclass definitions for all JSON files in a folder and create a master file.

    Args:
        input_folder (str): Path to the folder containing JSON files.
        output_dir (str): Directory to store the generated Python files.
        master_file_path (str): Path to the master file that imports all generated files.
    """
    input_folder_path = Path(input_folder)
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    import_lines = []

    for json_file in input_folder_path.glob("*.json"):
        output_file = output_dir_path / f"{json_file.stem}.py"
        generate_dataclasses_from_json(str(json_file), str(output_file))

        module_name = output_file.stem
        import_lines.append(f"from .{module_name} import *")

    with open(master_file_path, "w", encoding="utf-8") as file:
        file.write('"""\nThis module imports all generated models.\n"""\n')
        file.write("\n".join(import_lines))
        file.write("\n\n__all__ = [")
        file.write(
            ", ".join(
                f'"{json_file.stem}"' for json_file in input_folder_path.glob("*.json")
            )
        )
        file.write("]\n")


if __name__ == "__main__":
    # Folder containing JSON files
    JSON_FOLDER = "defs/json"

    # Directory to store the generated Python files
    OUTPUT_DIRECTORY = "defs"

    # Master file to import all generated files
    MASTER_FILE = "defs/__init__.py"

    with open(MASTER_FILE, "w", encoding="utf-8") as f:
        # Generate the dataclasses and the master file
        generate_definitions_and_master(JSON_FOLDER, OUTPUT_DIRECTORY, MASTER_FILE)

    print(
        f"Dataclasses and enums have been generated for each JSON file in {JSON_FOLDER} and saved in {OUTPUT_DIRECTORY}."
    )
    print(f"A master file has been created at {MASTER_FILE}.")

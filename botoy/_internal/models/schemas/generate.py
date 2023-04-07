if __name__ == "__main__":
    from pathlib import Path

    from datamodel_code_generator import InputFileType, generate

    script_path = Path(__file__).parent
    out_path = script_path.parent

    for json_schema in script_path.iterdir():
        if not json_schema.suffix.endswith("json"):
            continue
        print(json_schema)
        generate(
            json_schema,
            input_file_type=InputFileType.JsonSchema,
            output=out_path / f"{json_schema.stem}.py",
        )

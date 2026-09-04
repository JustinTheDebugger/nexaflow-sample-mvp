from datetime import date

from repositories.sample_repository import (
    create_sample,
    get_sample_types,
)


def main():
    print("Sample types:")

    sample_types = get_sample_types()

    for sample_type in sample_types:
        print(
            sample_type["code"],
            "-",
            sample_type["name"],
        )

    pp_type = next(
        sample_type
        for sample_type in sample_types
        if sample_type["code"] == "PP"
    )

    print("\nCreating test sample...")

    sample = create_sample(
        product_name="Database Test Sample",
        product_code="TEST-001",
        category="Tent",
        sample_type_id=pp_type["id"],
        source="Factory",
        received_date=date.today(),
        current_location="Warehouse A · Test Rack",
        condition="Good",
        notes="Temporary NeonDB persistence test.",
    )

    print("Created successfully:")
    print(sample)


if __name__ == "__main__":
    main()
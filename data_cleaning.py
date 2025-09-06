import pandas as pd

def clean_canteen_data(input_filepath, output_filepath):
    """
    A simple data cleaning script for the canteen CSV data.
    - Fills missing 'category' with 'general'.
    - Ensures 'price' is a positive number.
    - Capitalizes 'name' and 'category'.
    """
    try:
        df = pd.read_csv(input_filepath)
        print(f"Loaded {input_filepath} with {len(df)} rows.")

        # Handle missing categories
        if 'category' in df.columns:
            initial_missing = df['category'].isnull().sum()
            if initial_missing > 0:
                df['category'].fillna('general', inplace=True)
                print(f"Filled {initial_missing} missing categories with 'general'.")
            # Capitalize category names
            df['category'] = df['category'].str.capitalize()

        # Ensure price is a positive float
        if 'price' in df.columns:
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            df.dropna(subset=['price'], inplace=True) # Drop rows where price is not a number
            df = df[df['price'] > 0]
            print(f"Validated price column. Data now has {len(df)} rows.")

        # Capitalize dish names
        if 'name' in df.columns:
            df['name'] = df['name'].str.title()
            
        df.to_csv(output_filepath, index=False)
        print(f"Cleaned data saved to {output_filepath}.")

    except FileNotFoundError:
        print(f"Error: The file {input_filepath} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    # Example usage:
    # Create a dummy CSV with issues to test the cleaning script
    dummy_data = {
        'dish_id': [1, 2, 3, 4],
        'name': ['test pizza', 'old burger', 'bad soup', 'good salad'],
        'category': ['italian', None, 'soup', 'salad'],
        'price': [9.99, 'invalid', -5.00, 7.50]
    }
    dummy_df = pd.DataFrame(dummy_data)
    dummy_df.to_csv('dummy_dirty_data.csv', index=False)

    print("--- Running cleaning script on dummy data ---")
    clean_canteen_data('dummy_dirty_data.csv', 'cleaned_canteen_data.csv')

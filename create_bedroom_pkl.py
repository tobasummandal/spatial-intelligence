import pickle
import os

# Path to your bedroom.obj file
object_paths = [os.path.abspath('bedroom.obj')]

# Save to pickle file
with open('bedroom_object_path.pkl', 'wb') as f:
    pickle.dump(object_paths, f)

print(f"Created bedroom_object_path.pkl with path: {object_paths[0]}")

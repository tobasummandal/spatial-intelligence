import pickle
import os

# Path to your apple.obj file
object_paths = [os.path.abspath('apple.obj')]

# Save to pickle file
with open('apple_object_path.pkl', 'wb') as f:
    pickle.dump(object_paths, f)

print(f"Created apple_object_path.pkl with path: {object_paths[0]}")

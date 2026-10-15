# download_dataset.py
import os
import shutil
import kagglehub

print("🌱 Plant Disease Dataset Downloader")
print("=" * 50)

# Try multiple dataset sources
datasets = [
    "vipoooool/new-plant-diseases-dataset",  # Large dataset
    "emmarex/plantdisease",  # PlantVillage
]

downloaded = False

for dataset in datasets:
    try:
        print(f"\n📥 Trying to download: {dataset}")
        
        # Download dataset
        path = kagglehub.dataset_download(dataset)
        print(f"✅ Downloaded to: {path}")
        
        # Create dataset folder
        os.makedirs('dataset', exist_ok=True)
        
        # Copy files
        if os.path.exists(path):
            for item in os.listdir(path):
                src = os.path.join(path, item)
                dst = os.path.join('dataset', item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                    print(f"📁 Copied folder: {item}")
                else:
                    shutil.copy2(src, dst)
                    print(f"📄 Copied file: {item}")
        
        downloaded = True
        break
        
    except Exception as e:
        print(f"❌ Failed to download {dataset}: {e}")
        continue

if not downloaded:
    print("\n❌ All download attempts failed.")
    print("\n📝 Manual download option:")
    print("   1. Go to: https://www.kaggle.com/datasets/vipoooool/new-plant-diseases-dataset")
    print("   2. Click 'Download' button")
    print("   3. Extract the zip file to 'dataset' folder")
else:
    print("\n✅ Dataset ready!")
    print("\n📁 Dataset structure:")
    if os.path.exists('dataset'):
        for item in os.listdir('dataset')[:10]:
            print(f"   - {item}")
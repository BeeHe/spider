import os
import traceback
from PIL import Image
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True


def make_img_into_half(path, chapter_name, img_name):
    img_path = os.path.join(path, chapter_name, img_name)
    img = Image.open(img_path)
    weight, height = img.size
    try:
        img_1 = img.crop((0, 0, weight / 2, height))
        img_2 = img.crop((weight / 2, 0, weight, height))
    except Exception as e:
        exstr = traceback.format_exc()
        print(exstr)
        print("error: ", type(img), weight, height)

    img1_name = '_a.'.join(img_name.split('.'))
    img2_name = '_b.'.join(img_name.split('.'))
    if not os.path.exists(os.path.join(path, chapter_name + '_half')):
        os.makedirs(os.path.join(path, chapter_name + '_half'))
    img_1.save(os.path.join(path, chapter_name + '_half', img1_name))
    img_2.save(os.path.join(path, chapter_name + '_half', img2_name))
    # print('saved img: ', img_name)


def main():
    base_path = '/Users/HeBee/Downloads/hunter'
    vol_list = [
            vol for vol in os.listdir(base_path)
            if '卷' in vol and 'half' not in vol
    ]
    for vol_name in vol_list:
        vol_path = os.path.join(base_path, vol_name)
        img_list = os.listdir(vol_path)
        print('start transfer img: ', img_list)
        for img_name in img_list:
            make_img_into_half(base_path, vol_name, img_name)
        print("vol: %s finished" % vol_name)


if __name__ == "__main__":
    main()


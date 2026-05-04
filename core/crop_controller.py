from PIL import Image


class CropController:
    def crop(self, image: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
        left, top, right, bottom = box
        left = max(0, min(left, image.width - 1))
        top = max(0, min(top, image.height - 1))
        right = max(left + 1, min(right, image.width))
        bottom = max(top + 1, min(bottom, image.height))
        if right - left < 2 or bottom - top < 2:
            raise ValueError("裁剪区域过小，无法应用。")
        return image.crop((left, top, right, bottom))

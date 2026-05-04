from PIL import Image


class TransformController:
    def resize_keep_aspect(self, image: Image.Image, width: int) -> Image.Image:
        width = max(1, int(width))
        ratio = width / image.width
        height = max(1, round(image.height * ratio))
        return image.resize((width, height), Image.LANCZOS)

    def stretch(self, image: Image.Image, width: int, height: int) -> Image.Image:
        width = max(1, int(width))
        height = max(1, int(height))
        return image.resize((width, height), Image.LANCZOS)

    def proportional_height(self, image: Image.Image, width: int) -> int:
        width = max(1, int(width))
        return max(1, round(image.height * (width / image.width)))

    def proportional_width(self, image: Image.Image, height: int) -> int:
        height = max(1, int(height))
        return max(1, round(image.width * (height / image.height)))

    def rotate(self, image: Image.Image, angle: float, expand: bool = True) -> Image.Image:
        return image.rotate(-float(angle), resample=Image.BICUBIC, expand=expand)

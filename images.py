import logging
import math

from cStringIO import StringIO

from PIL import Image, ImageDraw, ImageFont

SIZE = 1000000

FONT = "pil_resources/NewFont.ttf"

TOWN_HALL_VALUES = {
    1: [375, 0, 20],
    2: [1500, 0, 20],
    3: [25000, 0, 20],
    4: [125000, 0, 18],
    5: [198000, 0, 16],
    6: [198000, 0, 12],
    7: [198000, 1000, 10],
    8: [198000, 2000, 8],
    9: [198000, 2000, 4],
    10: [198000, 2000, 2],
}


def create_base_image(base_image, town_hall_level):
    # figure out the file size
    base_image.file.seek(0, 2)
    size = base_image.file.tell()
    base_image.file.seek(0)

    # load into images
    img = Image.open(StringIO(base_image.file.read()))

    # reduce size as needed
    width, height = img.size
    logging.info("height: {} width: {}".format(width, height))

    create_boxes_and_text(img, town_hall_level)
    img = shrink_image(img)

    image_buffer = StringIO()
    img.save(image_buffer, format='JPEG')
    # return the image
    image_buffer.seek(0, 2)
    logging.info("size is {}".format(image_buffer.tell()))
    if image_buffer.tell() > SIZE:
        raise ArithmeticError("Too large!")
    image_buffer.seek(0)
    return image_buffer.read()


def shrink_image(img):
    image_buffer = StringIO()
    img.save(image_buffer, format='JPEG')
    image_buffer.seek(0, 2)
    logging.info("size is {}".format(image_buffer.tell()))
    size = image_buffer.tell()
    i = 0
    while size > SIZE and i < 10:
        i += 1
        width, height = img.size
        logging.info("height: {} width: {}".format(width, height))
        logging.info("Image too large: {}".format(size))
        per_to_reduce = math.sqrt(float(SIZE)/size)
        logging.info("multiply by {}".format(per_to_reduce))
        new_width = int(width * per_to_reduce)
        new_height = int(height * per_to_reduce)
        logging.info("new height: {} new width: {}".format(new_width, new_height))
        img = img.resize((new_width, new_height))
        image_buffer = StringIO()
        img.save(image_buffer, format='JPEG')
        image_buffer.seek(0, 2)
        logging.info("size is {}".format(image_buffer.tell()))
        size = image_buffer.tell()
    return img


def create_boxes_and_text(img, town_hall_level):
    gold = "{}G".format(TOWN_HALL_VALUES[town_hall_level][0])
    elixer = "{}E".format(TOWN_HALL_VALUES[town_hall_level][0])
    dark_e = "{}DE".format(TOWN_HALL_VALUES[town_hall_level][1])
    trophies = "{}T".format(TOWN_HALL_VALUES[town_hall_level][2])

    width, height = img.size
    box_height = int(height * .25)
    box_width = int(width * .25)

    draw = ImageDraw.Draw(img)

    fontsize = 1  # starting font size
    # portion of image width you want text width to be

    logging.info(FONT)
    draw_font = ImageFont.truetype(FONT, fontsize)
    while draw_font.getsize(gold)[0] < .5 * box_width:
        # iterate until the text size is just larger than the criteria
        fontsize += 1
        draw_font = ImageFont.truetype(FONT, fontsize)

    # optionally de-increment to be sure it is less than criteria

    #upper left
    draw.rectangle(
        ((0, 0), (box_width, box_height)),
        fill='black',
        outline='black')
    draw.text(
        (box_height * .25, box_width / 2 - draw_font.getsize(gold)[0] / 2),
        gold,
        fill='gold',
        font=draw_font
    )

    #botton left
    draw.rectangle(
        ((0, height - box_height), (box_width, height)),
        fill='black',
        outline='black')
    draw.text(
        (box_width / 2 - draw_font.getsize(elixer)[0] / 2, height - box_height * .65),
        elixer,
        fill='purple',
        font=draw_font
    )

    # upper right
    draw.rectangle(
        ((width - box_width, 0), (width, box_height)),
        fill='black',
        outline='black'
    )
    draw.text(
        (width - box_width / 2 - draw_font.getsize(dark_e)[0] / 2, box_height / 2 - draw_font.getsize(dark_e)[1] / 2),
        dark_e,
        fill='white',
        font=draw_font
    )

    # bottom right
    draw.rectangle(
        ((width - box_width, height - box_height), (width, height)),
        fill='black',
        outline='black'
    )
    draw.text(
        (width - box_width / 2 - draw_font.getsize(trophies)[0] / 2, (height - box_height /2 - draw_font.getsize(trophies)[1] / 2)),
        trophies,
        fill='gold',
        font=draw_font
    )

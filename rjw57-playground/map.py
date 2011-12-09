import sys

from PIL import Image
from tracker import Tracker

def main():
  t = Tracker(*sys.argv[1:3])
  for f in sys.argv[3:]:
    t.new_image(Image.open(f).convert('RGB'))
  Image.fromarray(t.recon_image()).save('foo.png')

if __name__ == '__main__':
  main()

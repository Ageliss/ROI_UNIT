#!/usr/bin/env python
'''
ROI Constraint UNIT
Bicheng Luo (UNI:bl2679)
Training script of ROI (Region of Interest) Constraint UNIT. I basically add a ROI generator and discriminator to enforce cycle consistency to the cropped image domains.
'''
from __future__ import print_function
from common import get_data_loader, prepare_snapshot_and_image_folder, write_html, write_loss
from tools import *
from trainers import *
from datasets import *
import sys
import torchvision
from itertools import izip
import tensorboard
from tensorboard import summary
from optparse import OptionParser
parser = OptionParser()
parser.add_option('--gpu', type=int, help="gpu id", default=0)
parser.add_option('--resume', type=int, help="resume training?", default=0)
parser.add_option('--config', type=str, help="net configuration")
parser.add_option('--log', type=str, help="log path")
parser.add_option('--roi', type=str, help='region of interests (x,y,w,h)')

MAX_EPOCHS = 100000

#bl2679
def main(argv):
  (opts, args) = parser.parse_args(argv)

  # Load experiment setting
  assert isinstance(opts, object)
  config = NetConfig(opts.config)

  batch_size = config.hyperparameters['batch_size']
  max_iterations = config.hyperparameters['max_iterations']

  train_loader_a = get_data_loader(config.datasets['train_a'], batch_size)
  train_loader_b = get_data_loader(config.datasets['train_b'], batch_size)

  # Parse ROI parameters
  roi = [int(val_str) for val_str in opts.roi.split(',')]
  roi_x = roi[0]
  roi_y = roi[1]
  roi_w = roi[2]
  roi_h = roi[3]

  cmd1 = "trainer=%s(config.hyperparameters)" % config.hyperparameters['trainer']
  cmd2 = "roi_trainer=%s(config.hyperparameters)" % config.hyperparameters['trainer']
  local_dict = locals()
  exec(cmd1, globals(), local_dict)
  trainer = local_dict['trainer']
  exec(cmd2, globals(), local_dict)
  roi_trainer = local_dict['roi_trainer']

  # Check if resume training
  iterations = 0
  if opts.resume == 1:
    iterations = trainer.resume(config.snapshot_prefix)
    roi_trainer.resume(config.snapshot_prefix)
  trainer.cuda(opts.gpu)
  roi_trainer.cuda(opts.gpu)

  ######################################################################################################################
  # Setup logger and repare image outputs
  train_writer = tensorboard.FileWriter("%s/%s" % (opts.log,os.path.splitext(os.path.basename(opts.config))[0]))
  image_directory, snapshot_directory = prepare_snapshot_and_image_folder(config.snapshot_prefix, iterations, config.image_save_iterations)

  for ep in range(0, MAX_EPOCHS):
    for it, (images_a, images_b) in enumerate(izip(train_loader_a,train_loader_b)):
      if images_a.size(0) != batch_size or images_b.size(0) != batch_size:
        continue
      
      # Crop images according to ROI
      roi_images_a = images_a[:, :, roi_y:roi_y+roi_h, roi_x:roi_x+roi_w].clone()
      roi_images_b = images_b[:, :, roi_y:roi_y+roi_h, roi_x:roi_x+roi_w].clone()

      roi_images_a = Variable(roi_images_a.cuda(opts.gpu))
      roi_images_b = Variable(roi_images_b.cuda(opts.gpu))

      images_a = Variable(images_a.cuda(opts.gpu))
      images_b = Variable(images_b.cuda(opts.gpu))

      # Main training code
      trainer.dis_update(images_a, images_b, config.hyperparameters)
      trainer.gen_update(images_a, images_b, config.hyperparameters)

      # Training code for ROI
      roi_trainer.dis_update(roi_images_a, roi_images_b, config.hyperparameters)
      roi_image_outputs = roi_trainer.gen_update(roi_images_a, roi_images_b, config.hyperparameters)
      roi_assembled_images = roi_trainer.assemble_outputs(roi_images_a, roi_images_b, roi_image_outputs)

      # Paste ROI to original images to update generator
      x_aa, x_ba, x_ab, x_bb, shared = trainer.gen(images_a, images_b)
      x_ba_paste = x_ba.clone()
      x_ab_paste = x_ab.clone()
      x_ba_paste[:, :, roi_y:roi_y+roi_h, roi_x:roi_x+roi_w] = roi_image_outputs[1].clone()
      x_ab_paste[:, :, roi_y:roi_y+roi_h, roi_x:roi_x+roi_w] = roi_image_outputs[2].clone()
      trainer.gen.zero_grad()
      image_outputs = trainer.gen_update_helper(images_a, images_b, x_aa, x_ba_paste, x_ab_paste, x_bb, shared, config.hyperparameters)
      assembled_images = trainer.assemble_outputs(images_a, images_b, image_outputs)

      # Dump training stats in log file
      if (iterations+1) % config.display == 0:
        write_loss(iterations, max_iterations, trainer, train_writer)

      if (iterations+1) % config.image_save_iterations == 0:
        img_filename = '%s/gen_%08d.jpg' % (image_directory, iterations + 1)
        torchvision.utils.save_image(assembled_images.data / 2 + 0.5, img_filename, nrow=1)
        img_filename = '%s/roi_gen_%08d.jpg' % (image_directory, iterations + 1)
        torchvision.utils.save_image(roi_assembled_images.data / 2 + 0.5, img_filename, nrow=1)
        write_html(snapshot_directory + "/index.html", iterations + 1, config.image_save_iterations, image_directory)
      elif (iterations + 1) % config.image_display_iterations == 0:
        img_filename = '%s/gen.jpg' % (image_directory)
        torchvision.utils.save_image(assembled_images.data / 2 + 0.5, img_filename, nrow=1)
        img_filename = '%s/roi_gen.jpg' % (image_directory)
        torchvision.utils.save_image(roi_assembled_images.data / 2 + 0.5, img_filename, nrow=1)

      # Save network weights
      if (iterations+1) % config.snapshot_save_iterations == 0:
        trainer.save(config.snapshot_prefix, iterations)

      iterations += 1
      if iterations >= max_iterations:
        return

if __name__ == '__main__':
  main(sys.argv)


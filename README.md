# ROI Constraint UNIT

## Baseline Method
* UNIT: UNsupervised Image-to-image Translation Networks
* GitHub repo: https://github.com/mingyuliutw/UNIT
* Paper link: https://arxiv.org/abs/1703.00848

## Organization of Codes
- The original UNIT
    - `datasets`
        Directory for different kinds of image loaders, defined in the original UNIT
    - `tools`
        Directory for training configuration loading, defined in the original UNIT
    - `trainers`
        Directory for the implementation of different netwokrs, generators, discriminators and encoders
    - `cocogan_train_domain_adaptation.py`
        Training scirpt for implementing domain adaptation
    - `cocogan_translate_one_image.py`
        Inference script for translating one image to the other domain
    - `cocogan_translate.py`
        Inference script for translating all images from image loader to the other domain
    - `common.py`
        A helper script for training utilization 
- My improvement
    - `cocogan_train_roi.py`
        Training script of ROI (Region of Interest) Constraint UNIT. I basically add a ROI generator and discriminator to enforce cycle consistency to the cropped image domains.
    - `trainers/cocgan_trainer.py`
        A script for implementing the weight update operation of generators and discriminators. I modified the weight update function to adapt to our needs.
    - `run_same_image_for_iterations.py`
        A script to generate image translation results for multiple generators
    - `run_same_net_for_images.py`
        A script to generate multiple image translation results using a specific generator

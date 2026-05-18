# Gaze-Assisted Medical Image Segmentation

Source: thesis_Khaertdinova.pdf

Converted to Markdown for use with Claude Code. Page boundaries are preserved as HTML comments.


<!-- Page 1 -->

Автономная некоммерческая организация высшего образования
«Университет Иннополис»

ВЫПУСКНАЯ КВАЛИФИКАЦИОННАЯ РАБОТА
(БАКАЛАВРСКАЯ РАБОТА)
по направлению подготовки
#### 09.03.01 - «Информатика и вычислительная техника»

GRADUATION THESIS
(BACHELOR’S GRADUATION THESIS)
Field of Study
#### 09.03.01 – «Computer Science»

Направленность (профиль) образовательной программы
«Информатика и вычислительная техника»
Area of Specialization / Academic Program Title:
«Computer Science»

Тема /
Topic
 Сегментация Медицинских Изображений с Помощью Взгляда /
Gaze-Assisted Medical Image Segmentation

Работу выполнила /
Thesis is executed by

 Хаертдинова Лейла
Альбертовна / Khaertdinova
Leila Albertovna

подпись / signature

Руководитель
выпускной
квалификационной
работы /
Supervisor of
Graduation Thesis

 Лукманов Рустам
Абубакирович / Lukmanov
Rustam Abubakirovich

подпись / signature

Консультанты /
Consultants

подпись / signature

Иннополис, Innopolis, 2025


<!-- Page 2 -->

## Contents
Introduction
1.1
Medical Image Segmentation: Context and Applications
. . . .
1.2
Research Questions . . . . . . . . . . . . . . . . . . . . . . . .
1.3
Chapter Summary . . . . . . . . . . . . . . . . . . . . . . . . .
Literature Review
2.1
Background on Medical Image Segmentation
. . . . . . . . . .
2.1.1
Image Segmentation . . . . . . . . . . . . . . . . . . .
2.1.2
Interactive Image Segmentation . . . . . . . . . . . . .
2.2
Medical Image Segmentation . . . . . . . . . . . . . . . . . . .
2.2.1
Classical Approaches . . . . . . . . . . . . . . . . . . .
2.2.2
Deep Learning-based Approaches . . . . . . . . . . . .
Methodology
3.1
Problem Formulation . . . . . . . . . . . . . . . . . . . . . . .
3.2
Model Architecture . . . . . . . . . . . . . . . . . . . . . . . .
3.3
Model Training on Synthetic Gaze Data . . . . . . . . . . . . .
3.3.1
Fine-tuning MedSAM
. . . . . . . . . . . . . . . . . .
3.3.2
Gaze Prompts Generation
. . . . . . . . . . . . . . . .


<!-- Page 3 -->

CONTENTS
3.4
Model Training on Mouse Clicks . . . . . . . . . . . . . . . . .
3.5
Training Details . . . . . . . . . . . . . . . . . . . . . . . . . .
3.6
Dataset
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
Experimental Setup
4.1
Radiology Workstation . . . . . . . . . . . . . . . . . . . . . .
4.1.1
Eye Calibration . . . . . . . . . . . . . . . . . . . . . .
4.1.2
Eye Tracking Software . . . . . . . . . . . . . . . . . .
4.2
Software and Hardware Requirements . . . . . . . . . . . . . .
Experimental Results
5.1
Gaze Points Selection . . . . . . . . . . . . . . . . . . . . . . .
5.2
Benchmarking . . . . . . . . . . . . . . . . . . . . . . . . . . .
5.3
Clinical Evaluation . . . . . . . . . . . . . . . . . . . . . . . .
5.3.1
Comparison with Existing Tools . . . . . . . . . . . . .
5.3.2
Segmentation Correction Using Gaze . . . . . . . . . .
Discussion
6.1
Organ-Level Segmentation Analysis . . . . . . . . . . . . . . .
6.2
Medical Expert Validation
. . . . . . . . . . . . . . . . . . . .
6.3
Clinical Practice . . . . . . . . . . . . . . . . . . . . . . . . . .
6.4
Limitations and Future Work . . . . . . . . . . . . . . . . . . .
6.5
Ethical Statement . . . . . . . . . . . . . . . . . . . . . . . . .
Conclusion
## Bibliography


<!-- Page 4 -->

CONTENTS
## A Prerequisite Concepts
A.1
Deep Learning Essentials . . . . . . . . . . . . . . . . . . . . .
A.2
Computer Vision Architectures . . . . . . . . . . . . . . . . . .
B
Defining optimal prompts
B.1
Evaluation on Synthetic Data . . . . . . . . . . . . . . . . . . .
B.2
Evaluation with Clinicians . . . . . . . . . . . . . . . . . . . .


<!-- Page 5 -->

## Abstract
Medical image segmentation is a crucial part of various diagnostic applications, such as cancer screening and radiotherapy planning. Manual annotation of
patient organs is labor-intensive and time-consuming, while modern automated
techniques have not yet reached levels sufficient for clinical adoption. This research aims to enhance the accuracy and efficiency of segmentation, ultimately
improving clinical outcomes. We investigate a semi-supervised medical image
segmentation using eye gaze as interactive input for segmentation correction. In
particular, we propose a lightweight fine-tuning approach of the Segment Anything Model in medical images (MedSAM) to adjust segmentation masks using
gaze prompts. We also present a model that enables interactive medical segmentation using mouse clicks. Our models are trained on the publicly available WORD
dataset, comprising 120 abdominal CT scans across 16 organs. Experimental
results demonstrate that our gaze-assisted MedSAM outperforms state-of-the-art
automated and interactive segmentation approaches, with an 11% improvement in
an average Dice coefficient. Compared to manual drawing, click-based and bounding box-based tools, our gaze-assisted method yields an approximately 1.5% gain
in accuracy and reduces annotation time by over 50%. For challenging cases, gaze
corrections improve segmentation quality by up to 62% compared to traditional
segmentation methods based on bounding boxes. Our innovative approach shows
promise for integrating eye-tracking into interactive medical segmentation and
opens the door for new advancements in human-AI collaboration in medicine.


<!-- Page 6 -->

## Chapter 1: Introduction
1.1
Medical Image Segmentation: Context and Applications
The workload of radiologists has increased significantly in the last several
decades, raising concerns about the impact of clinical fatigue on the precision of
medical image interpretation [1], [2]. To address the risk of decreased diagnostic
quality, various strategies have been proposed, including limiting workloads and
optimizing workflows [3]. Among these strategies, Artificial Intelligence (AI) has
emerged as a particularly promising solution. AI technologies, particularly Deep
Learning, have the potential to improve the efficiency and accuracy of medical
image analysis, thus helping to reduce some of the burdens faced by radiologists.
Medical image segmentation is a fundamental task in this context, as it
involves partitioning images into meaningful regions that provide essential information for clinical diagnosis and patient monitoring. Precise segmentation is
especially vital in therapeutic interventions, such as radiation therapy for cancer


<!-- Page 7 -->

### 1.1 Medical Image Segmentation: Context and Applications
treatment [4], [5]. The advent of Deep Learning has revolutionized the automatic
segmentation of medical images, significantly simplifying the annotation process
and reducing the labor-intensive nature of manual segmentation [6]. However,
automated segmentation has not yet reached levels sufficient for clinical adoption.
Therefore, inaccuracies in the predicted segmentation results often require manual
corrections, which remain labor-intensive and time-consuming.
Recent developments in interactive segmentation have improved the efficiency of the correction process in various domains, including medicine, allowing adjustments to be made with just a few mouse clicks [7]. Unlike existing
approaches that incorporate user corrections through bounding boxes [7], [8],
points [9], [10], or scribbles [11], an alternative method that uses gaze data can
provide vital supervision signals that are essential for medical images characterized by ambiguous boundaries and low contrast. Furthermore, gaze-assisted
segmentation has shown a significant increase in efficiency, operating approximately twice as fast as traditional click-based methods [12].
By facilitating
immediate corrections based on the domain expert’s visual focus, gaze assistance
may prove to be a more effective alternative to traditional interactive methods for
the segmentation task.
This work is part of research in close collaboration with the Medical AI
Lab at Innopolis University and radiologists from a public oncology hospital in
Kazan, Republic of Tatarstan. It extends our two publications [13], [14] and
contributes new methods and evaluations focused on integrating eye gaze data
and mouse clicks into the interactive segmentation of medical images. In particular, we explore lightweight fine-tuning of the foundation model for interactive
segmentation, namely Medical Segment Anything Model, or MedSAM [7]. We
propose a novel approach that leverages gaze information to enhance the accuracy


<!-- Page 8 -->

### 1.2 Research Questions
Fig. 1.1.
Gaze-assisted segmentation system for radiologists, developed and
integrated within the workstation at our institution.
and efficiency of interactive medical image segmentation, with a focus on abdominal Computed Tomography (CT) scans, where precise segmentation is critical
for cancer treatment and radiotherapy planning. To support clinical use, we also
developed and integrated our gaze-assisted model into a radiology workstation
system, aiming to assist radiologists in analyzing and segmenting medical images
more efficiently (see Fig. 1.1).
1.2
Research Questions
In collaboration with medical experts, particularly through consultations
with radiologists from an oncology hospital, the challenges associated with the
segmentation task in medical imaging are investigated. As stated by radiologists,
they still perform manual segmentation using drawing tools. This process can be


<!-- Page 9 -->

### 1.2 Research Questions
time-consuming, taking up to roughly 5-10 hours for a single patient case that
can be one volumetric CT scan of the patient encompassing multiple organs and
tumors. This underscores a significant need for more efficient annotation tools
that can be developed with the use of AI.
While investigating existing interactive tools for medical segmentation, we
examined the method based on bounding boxes. Although this approach appears
to be faster than manual drawing, it still requires user effort and may struggle with
complex or ambiguous anatomical structures. Looking for a simpler interaction
modality, we initially considered mouse clicks as an alternative form of user input,
which proved to be more efficient but less intuitive for clinical scenarios. Building
on these insights, we introduced a gaze-assisted segmentation tool that seamlessly
tracks radiologists’ eye movements during image analysis. By leveraging gaze
data as an implicit form of user guidance, this tool enables semi-automated
segmentation, presenting a novel approach to improve radiologists’ routine work.
The proposed gaze-assisted method offers a more intuitive and accurate alternative
to other interactive techniques, including manual drawing and bounding boxes.
The main objective of this work is to combine state-of-the-art Deep Learningbased models with human interactive input in the form of eye gaze streams to
address the challenges of Interactive Medical Image Segmentation. The methods
introduced in this work aim to enhance the accuracy and efficiency of segmentation
processes, ultimately improving clinical outcomes.
In this work, the following research questions are examined:
• Research Question 1 (RQ1): How to effectively incorporate eye gaze data
into existing interactive segmentation frameworks to improve the accuracy
of medical image segmentation?


<!-- Page 10 -->

### 1.2 Research Questions
• Research Question 2 (RQ2): How does the performance of gaze-assisted
segmentation compare to traditional methods, such as drawing, mouse clicks
and bounding boxes, in terms of efficiency and accuracy?
To address these research questions, we fine-tuned the MedSAM model using
synthetic gaze data and click points and evaluated the segmentation performance
and efficiency on an open-source abdominal CT benchmark, collaborating closely
with clinical experts. The trained models were deployed and evaluated within a
realistic radiology workstation equipped with an eye-tracking device.
For RQ1, the experimental results demonstrated that gaze data can be effectively used as point prompts for guiding the MedSAM model. More specifically,
these prompts were created by randomly selecting points from the eye-tracking
history and labeling them as foreground point prompts for MedSAM, enabling it
to generate accurate segmentation masks with minimal user intervention.
For RQ2, the gaze-assisted approach outperformed the state-of-the-art automated segmentation models and the MedSAM model that uses bounding box
prompts, achieving up to an 11% improvement in segmentation performance. As
the result of real-time experiments conducted in collaboration with clinical specialists, our gaze-assisted method also surpassed interactive methods, including
manual drawing, mouse clicks, and bounding boxes, demonstrating an improvement in segmentation accuracy of approximately 1.5%. In terms of efficiency,
the gaze-assisted approach reduced annotation time by more than half compared
to traditional methods, including manual drawing and bounding boxes. Furthermore, our model improved segmentation performance for cases with challenging
abdominal organ views, increasing accuracy by almost 1.5 times after correcting
the initial predictions made using original MedSAM with bounding boxes.


<!-- Page 11 -->

### 1.3 Chapter Summary
1.3
Chapter Summary
This thesis is organized into 6 chapters, including the current introductory
chapter. The emphasis of this work is placed on the development and evaluation
of a gaze-assisted approach for medical image segmentation, particularly in the
context of abdominal CT imaging used for cancer treatment planning.
The chapters are structured as follows:
• Chapter 1 provides a brief introduction, including general information
on medical image segmentation, the motivation behind this work, and the
research questions it aims to address.
• Chapter 2 presents prerequisite knowledge on basic Deep Learning concepts, introduces the task of interactive segmentation, and reviews prior
work in segmentation of medical images, starting from traditional segmentation techniques to contemporary Deep Learning-based approaches.
• Chapter 3 outlines the methodology employed in this research, including the problem formulation and justification of the selected models and
methods, as well as describes training details and the data used.
• Chapter 4 describes the experimental setup, information on the radiology
workstation and eye-tracking device, as well as provides an overview of the
hardware and software requirements.
• Chapter 5 presents the results of the experiments conducted. This chapter particularly contributes to RQ1 by identifying the most accurate gaze
selection strategy for the real-time application. It also addresses RQ2 by
evaluating the performance of our mouse click-based and gaze-assisted


<!-- Page 12 -->

### 1.3 Chapter Summary
segmentation methods against existing approaches, including modern automated segmentation models, the bounding box-based interactive method,
and the manual drawing widely exploited in hospitals.
• Chapter 6 provides a comprehensive discussion of our findings, their implications for clinical practice, the limitations and suggestions for future
research, and an ethical statement.
• Chapter 7 summarizes the main findings and contributions, as well as
outlines the potential impact of the research.
To promote reproducibility and encourage further research, the source code,
trained models, and demonstration video of the proposed system are made publicly
available. Interested readers can access the GitHub repository1 for the project
implementation and demo video2 showcasing its use in a real clinical setting.
1https://github.com/leiluk1/gaze-based-segmentation
2https://www.youtube.com/watch?v=DBO6wQAXhjw


<!-- Page 13 -->

## Chapter 2: Literature Review
The advancement of AI-based technologies has revolutionized the medical
field, offering unprecedented opportunities for automated diagnosis, treatment
planning, and disease monitoring.
At the heart of these innovations lies the
process of image segmentation, which is generally defined, e.g., in [15], as a
task for delineating regions of interest to extract meaningful information within
medical images. Image segmentation is an emerging task in the field of Computer
Vision, which has demonstrated a large number of developments over the last
decades.
These developments range from segmentation techniques based on
image transformations and edge detection to contemporary Deep Learning-based
methods, including interactive and promptable segmentation approaches powered
by the latest advances in AI.
This chapter provides background information in Section 2.1, outlining the
image segmentation for healthcare applications and the task of interactive image
segmentation. Section 2.2 then presents the evolution of segmentation methods
– from traditional techniques to cutting-edge Deep Learning models, including
modern interactive segmentation methods.


<!-- Page 14 -->

### 2.1 Background on Medical Image Segmentation
We also present a preliminary background on Deep Learning techniques
used in this study, such as loss functions, neural network training, gradient-based
optimization algorithms, convolutional and attention-based model architectures
in Appendix A.
2.1
Background on Medical Image Segmentation
2.1.1
Image Segmentation
Image segmentation is an essential task in Computer Vision that aims to partition an image into meaningful segments, specifically focusing on the extraction
of regions of interest (ROIs) from image data. An illustrative example provided in
Fig. 2.1 demonstrates the primary goal of image segmentation, highlighting area
of ROIs and producing their segmentation masks.
Fig. 2.1. An example of Magnetic Resonance Imaging (MRI) slice segmentation
(Figure 14, [16]).
The image segmentation process is particularly crucial in medical imaging,
as it facilitates the identification of anatomical structures and pathological regions
within the human body [17]. Besides, image segmentation can be used for organ
annotation, which is important for applications such as cancer treatment and
radiation therapy planning [18]. Organ segmentation relies on manual delineation
performed by experienced radiologists, a process that can be labor-intensive and


<!-- Page 15 -->

### 2.1 Background on Medical Image Segmentation
prone to inter-observer variability [6]. To reduce the total workload of radiologists,
automated segmentation techniques have been developed.
One pivotal architecture in image segmentation is the U-Net [19], especially
applicable to biomedical image segmentation. U-Net model features a U-shaped
design with a contracting path (encoder) and an expansive path (decoder), as
illustrated in Fig. 2.2.
Fig. 2.2. U-Net architecture (Fig. 1, [19]).
The contracting path of the U-Net captures context through repeated application of two layers of 3 × 3 convolutions, followed by ReLU activations and a
2 × 2 max-pooling with stride 2. This is how downsampling in the encoder part
of the model works, by reducing spatial dimensions while increasing the number
of feature channels. Subsequently, the expansive path involves upsampling of the
feature map by using 2 × 2 convolutions (up-convolutions) that halve the number
of feature channels and raise the spatial dimensions, a concatenation with the
corresponding feature map from the contracting path, and two 3 × 3 convolutions
with ReLU activations. This concatenation, also called a skip connection, en-


<!-- Page 16 -->

### 2.1 Background on Medical Image Segmentation
ables combining upsampled outputs from decoder layers with the high-resolution
features from the corresponding encoder layers, which makes the segmentation
output more accurate. The final output is a segmentation map that assigns a class
label to each pixel in the input image.
The U-Net has achieved strong performance on diverse biomedical tasks,
such as cell segmentation in microscopy images. Building on these advancements, numerous variations of U-Net have been proposed, including nnU-Net
[20], 3D U-Net [21], and Res-UNets [22], [23], and adapted to various medical segmentation tasks. Zhou et al. [24] introduced U-Net++ with re-designed
skip pathways by adding nested and dense skip connections to improve feature
propagation. Following this, U-Net++ enhanced the accuracy of U-Net in medical
applications, such as lung nodule and liver segmentation. To enhance model focus
on relevant regions, Oktay et al. [25] introduced Attention U-Net with attention
gates to highlight relevant features during the decoding part. Diakogiannis et al.
[23] proposed Res-UNet with residual connections for handling vanishing gradients and pyramid scene parsing pooling for deeper feature extraction. Another
segmentation framework built on the U-Net architecture, nnU-Net [20] underwent minor modifications like using the leaky ReLU activation function instead
of simple ReLU. This framework automatically adapted preprocessing, network
architecture, training, and postprocessing pipelines to a given dataset. nnU-Net
has achieved state-of-the-art results across more than 19 biomedical segmentation
benchmarks and is considered a strong baseline in the field.
Another frequently exploited framework, DeepLabV3+ [26], combines the
spatial pyramid pooling with an encoder-decoder architecture, enabling effective
multi-scale feature extraction and refined segmentation boundaries. While originally designed for natural images, DeepLabV3+ has been successfully adapted


<!-- Page 17 -->

### 2.1 Background on Medical Image Segmentation
for medical image segmentation, particularly in abdominal organ and skin lesion
segmentation [27].
Further advancements in medical image segmentation include incorporating Transformers through hybrid architectures. For instance, Chen et al. [28]
proposed TransUNet, which incorporates self-attention mechanisms into the UNet encoder via Transformer blocks.
TransUNet has improved the ability of
long-range dependencies and demonstrated strong performance on multi-organ
and cardiac segmentation tasks. Similarly, architectures such as nnFormer [29],
UNETR [30], and SwinUNETR [31] have extended Transformer integration to
enhance global feature representation into medical segmentation. For instance,
the ViT-based architecture of UNETR is depicted in Fig. 2.3. More recently, models like U-Mamba [32], inspired by U-Net and built upon state-space modeling
principles, have shown promising results across segmentation of diverse imaging
modalities, including abdominal CT, MRI, microscopy, and endoscopy images.
Fig. 2.3. UNETR architecture overview (Figure 1, [30]).


<!-- Page 18 -->

### 2.1 Background on Medical Image Segmentation
Despite these advancements, all automated methods are constrained by fixed
semantic classes and lack the flexibility to incorporate expert input. In high-stakes
domains like medicine, fully-automated segmentation remains insufficiently reliable for clinical deployment, often necessitating corrections made by medical
professionals. This highlights the need for interactive segmentation, which can
lead to more precise and accurate results.
2.1.2
Interactive Image Segmentation
Interactive image segmentation is a modification of the traditional image
segmentation task, designed to incorporate user input to guide and refine the
segmentation process.
Along with an image, a user may provide interactive
inputs, such as mouse clicks, contours, or bounding boxes, to correct segmentation
prediction errors. This technique is particularly beneficial in medical imaging,
where expert knowledge can significantly enhance segmentation accuracy.
With its roots in the pre-Deep Learning era, interactive segmentation has
progressed from techniques based on graph representations [33] and random
walks [34] to modern foundation models [7], [35]. In recent studies, various forms
of interactive input have been employed, such as clicks (RITM [9]), bounding
boxes (MedSAM [7], BoxInst [8]), and scribbles (ScribblePrompt [11]). Unlike
semantic or instance segmentation, interactive segmentation is not constrained
by fixed class labels and can segment objects from classes that have not been
previously seen, as this type of algorithm relies on user-provided commands to
perform the segmentation of any object class [9]. Another key advantage and
application of interactive segmentation is the ability to simplify and accelerate
data annotation, which is particularly beneficial for creating new datasets [36].


<!-- Page 19 -->

### 2.1 Background on Medical Image Segmentation
Segment Anything Model (SAM) [35] is a contemporary model in the domain of interactive segmentation, illustrated in Fig. 2.4. According to Fig. 2.5,
SAM architecture comprises a ViT-based image encoder, lightweight mask decoder, and prompt encoder that can process various interaction prompts: mouse
click coordinates, bounding boxes, masks, and text. SAM is considered a foundation model in the field, as it is a promptable and multimodal model, and has
demonstrated zero-shot performance across a diverse set of tasks, including image
segmentation and detection.
Fig. 2.4. SAM – foundation model for promptable segmentation (Figure 1a, [35]).
Fig. 2.5. SAM model overview (Figure 4, [35]).
While SAM has demonstrated impressive results on natural images, its effectiveness for medical images is less robust.
To address this, MedSAM [7]


<!-- Page 20 -->

### 2.1 Background on Medical Image Segmentation
was fine-tuned on a large-scale medical image dataset and specifically adapted
for medical image segmentation using bounding box prompts. MedSAM retains
the overall architecture of SAM, as illustrated in Fig. 2.6. The MedSAM model
comprises an image encoder, which is a Vision Transformer (ViT) with 12 transformer layers that generates image embeddings in a high-dimensional space. A
prompt encoder transforms user-provided bounding box coordinates into prompt
embeddings via positional encoding. Finally, the mask decoder fuses the image
and prompt embeddings using cross-attention, followed by convolutional layers
to produce the final segmentation output. Unlike SAM, MedSAM explicitly requires bounding boxes as input prompts. As an interactive segmentation model
tailored for a diverse set of medical imaging modalities, MedSAM showed a significant acceleration in the annotation process, reducing manual effort of experts
by approximately 83%.
Fig. 2.6. MedSAM model overview (Fig. 2b, [7]).
In the realm of interactive segmentation, various user input modalities have
been investigated. Traditional methods typically rely on interactive inputs in the
form of bounding boxes [7], [8], points [9], [10], or scribbles [11]. However,
incorporating gaze data offers crucial supervisory signals that are particularly
beneficial in the context of medical images, which often feature low contrast,


<!-- Page 21 -->

### 2.1 Background on Medical Image Segmentation
intensity variations, and ambiguous boundaries [37], [38]. Furthermore, eyetracking technology provides a novel input modality that captures the user’s visual
attention, which can introduce a more intuitive alternative to traditional methods.
Existing gaze-assisted approaches, such as GazeSAM [12], have shown
promise in reducing segmentation time while maintaining quality, although challenges remain in optimizing these systems for diverse clinical applications. In this
study, the authors utilized the original SAM to generate segmentation masks based
on a single gaze point. They compared gaze-based and click-based segmentation,
finding that gaze-based interaction was approximately twice as fast but yielded
slightly lower segmentation quality. However, the study did not explore the use
of multiple gaze points, leaving open questions about the system’s behavior when
gaze naturally shifts outside the region of interest – a common occurrence due to
involuntary gaze variance. By highlighting this gap, we aim to further investigate
the potential of gaze data for interactive medical image segmentation.
Overall, in recent years, numerous large architectures have been developed,
enabling to leverage their pre-trained weights for various downstream tasks. To
effectively utilize these pre-trained models, approaches such as transfer learning
and fine-tuning have emerged.
Transfer learning involves using a pre-trained
model as a starting point for a new task or domain. By freezing the parameters
of the pre-trained model, one can adapt it to the specific needs adding a classifier
that can be trained on a given dataset of interest. On the other hand, fine-tuning
refers to the process of further training the pre-trained model. Fine-tuning can
be seen as a specialized form of transfer learning, where the model is not only
reused but also refined to achieve optimal results in the new domain. In this work,
we will explore the fine-tuning of MedSAM [7] for click-based and gaze-assisted
medical segmentation.


<!-- Page 22 -->

### 2.2 Medical Image Segmentation
2.2
Medical Image Segmentation
2.2.1
Classical Approaches
Before the advent of Deep Learning, medical image segmentation relied
heavily on traditional techniques that utilized intrinsic image properties such as
contrast, texture, and histogram features. These methods included edge detection
[39], ROI-based thresholding [40], graph partitioning„ and random walks [41].
These approaches aimed to segment regions of interest (ROIs) directly from
the image data.
Later, hand-crafted features, such as Scale-Invariant Feature
Transform (SIFT) [42] gained popularity for improving the accuracy of medical
image segmentation.
While these early algorithms attracted significant interest for a while, they
often struggled to meet the precision and robustness required for clinical settings,
particularly in complex medical imaging scenarios [17].
2.2.2
Deep Learning-based Approaches
The introduction of Deep Learning has transformed medical image segmentation, enabling unprecedented accuracy and efficiency. The breakthrough began
in 2015 with the development of the U-Net, which introduced an encoder-decoder
architecture specifically designed for biomedical image segmentation [19]. Since
then, the U-Net framework has inspired a wide range of variants aimed at expanding its applicability, including 3D U-Net [21] in 2016, UNet++ [24] and Attention
U-Net [25] in 2018, ResUNet [23] in 2020, nnU-Net [20] and TransUNet [28]
in 2021. Furthermore, the DeepLabV3+ model [26], introduced in 2018, has
emerged as a strong baseline in this task.


<!-- Page 23 -->

### 2.2 Medical Image Segmentation
Recent advancements have incorporated innovative transformer-based architectures, introducing the self-attention concept and residual connections. These
ideas have further enhanced segmentation performance by improving feature representations. Notable examples include nnFormer [29] and SwinUNETR [31] in
2021, UNETR [30] in 2022, which have demonstrated significant improvements
in accuracy and adaptability for medical image segmentation.
Concurrently, there has been growing interest in interactive segmentation,
where user input, such as bounding boxes or scribbles, guides and corrects segmentation. This approach can be valuable in clinical practice, where precision
is essential and full automation remains unreliable. In 2024, interactive models
for medical segmentation, such as MedSAM [7] and Scribbleprompt [11], were
introduced. These approaches allow medical experts to provide prompts during the segmentation process and facilitate real-time adjustments. In particular,
MedSAM has demonstrated strong qualitative and quantitative results across a
wide range of modalities, including CT, MRI, ultrasound, and endoscopy. As
shown in Figs. 2.7 and 2.8, MedSAM outperforms SAM [35], U-Net [19], and
DeepLabV3+ [26] on external validation sets for various segmentation tasks.
Fig. 2.7. MedSAM visualized results compared to SAM [35], U-Net [19], and
DeepLabV3+ [26] for lymph node and fetal head segmentation (Fig. 3c, [7]).


<!-- Page 24 -->

### 2.2 Medical Image Segmentation
Fig. 2.8. MedSAM visualized results compared to SAM [35], U-Net [19], and
DeepLabV3+ [26] for cervical cancer and polyp segmentation (Fig. 3c, [7]).
Despite the progress in both fully automated and interactive segmentation
approaches for medical image segmentation, a critical gap remains in optimizing intuitive and efficient interaction with medical experts – particularly through
emerging modalities such as eye gaze. This work addresses that gap by investigating gaze-assisted and mouse click-based interactive segmentation, with the goal
of enhancing both the precision and usability of medical segmentation workflows.


<!-- Page 25 -->

## Chapter 3: Methodology
This chapter introduces the problem formulation in Section 3.1, focusing
on the notation of medical image segmentation and the objective of integrating
gaze data into the interactive system. Section 3.2 presents the model architecture.
Section 3.3 details the gaze-based training methods, including fine-tuning strategies for MedSAM and the incorporation of synthetic gaze data into the training
pipeline. Section 3.4 outlines the training procedure for the click-based segmentation model. In Sections 3.5 and 3.6, the training configurations and the dataset
used are described, respectively.
3.1
Problem Formulation
Medical image segmentation aims to partition an image into multiple anatomical structures, facilitating the identification of meaningful regions or areas of
interest. In the context of 3D CT scans, each volume, denoted as X, is associated
with a binary segmentation mask Y ∈{0, 1}H×W×D×C, where D represents the
number of slices in the CT volume along the z-axis, each slice with height H,


<!-- Page 26 -->

### 3.1 Problem Formulation
width W and number of channels C . In this binary mask, a value of 1 indicates
voxels (volume pixels) belonging to the target structure (e.g., the liver organ in
abdominal CT scans), while a value of 0 represents the background region.
A three-dimensional (3D) medical image, commonly acquired through medical imaging technologies such as computed tomography (CT) and magnetic resonance imaging (MRI), is defined as volumetric data that capture the organs and
anatomical structures of the human body in three dimensions. This study specifically focuses on the use of 3D CT images, on which segmentation adjustments are
validated using eye gaze data. Each 3D image is represented as X ∈RH×W×D×C,
where D denotes the number of slices, each with dimensions H × W, and C
represents the number of channels. Consequently, these volumetric CT scans can
be sliced into their respective 2D representations, expressed as ˆX ∈RH×W×C.
This work investigates interactive segmentation, a process that incorporates
user feedback to iteratively control and explicitly refine the predicted segmentation masks. More formally, interactive segmentation, also called promptable
segmentation, aims to return a segmentation mask given a segmentation prompt.
The prompt usually specifies the spatial information identifying the region of
interest. In particular, we focus on gaze prompts that can be recorded using an
eye-tracking device. The gaze stream is composed of coordinates (xt, yt) corresponding to the user’s pupil positions at the timestamp t. The objective of the
proposed gaze-assisted segmentation approach is to improve the segmentation
mask in real-time using a sequence of gaze points GT = {(xt, yt)}T
t=0, such that:
Q(M(X, GT)) > Q(M(X, GT′)),
(3.1)
where Q represents a quality metric (with higher values indicating better segmen-


<!-- Page 27 -->

### 3.2 Model Architecture
tation quality), M denotes the gaze-assisted segmentation model that generates
the mask Y, and GT′, where T′ < T, refers to the previous sequence of gaze points.
This formulation highlights the goal of enhancing segmentation performance by
integrating gaze data, thereby enabling domain experts to make more precise and
efficient segmentation adjustments in real time.
3.2
Model Architecture
Our framework is built on the MedSAM model [7], which is a contemporary
foundation model for interactive segmentation of medical images. Following the
MedSAM architecture, our model comprises three main components:
• Image encoder:
a Masked Autoencoder (MAE) [43] pre-trained ViT
model, specifically a ViT-Base/16 consisting of 12 transformer layers with
a patch size of 16x16. This encoder processes the input medical image and
computes a high-dimensional image embedding.
• Prompt encoder: transforms the input prompts into feature representations.
In our framework, gaze prompts are used as sparse point prompts, which
are represented by the sum of a positional encoding of the point location
and a learned embedding for a point label. The label specifies points as
"foreground" (label 1), "background" (label 0), or "not a point" (label -1).
• Lightweight mask decoder: maps the image embedding and prompt embedding to an output mask using cross-attention. The architecture of the
mask decoder is inspired by the Transformer decoder. To mitigate the ambiguity concerns, the mask decoder is developed to simultaneously predict


<!-- Page 28 -->

### 3.3 Model Training on Synthetic Gaze Data
three segmentation masks, along with Intersection over Union (IoU) scores
(in 3.6) for each of the masks.
We selected the final prediction as the
model’s most confident segmentation mask with the highest IoU.
3.3
Model Training on Synthetic Gaze Data
The proposed framework is designed to integrate eye gaze into the interactive
segmentation workflow. In this work, we fine-tuned the MedSAM model using
synthetic gaze prompts. This section provides a description of model fine-tuning
and gaze simulation strategy for training.
3.3.1
Fine-tuning MedSAM
Image
encoder
Mask
decoder
...
Prompt
encoder
Abdominal CT slice
Pancreas
segmentation mask
Gaze coordinates
Point prompt
Tuned
Frozen
Fig. 3.1. The proposed framework for gaze-assisted interactive segmentation of
medical images. An illustrative example shows the segmentation mask for the
pancreas organ, which is predicted based on input gaze coordinates serving as the
point prompt for MedSAM model.


<!-- Page 29 -->

### 3.3 Model Training on Synthetic Gaze Data
We used the standard MedSAM architecture, as depicted in Fig. 3.1. To
enhance the ability of the MedSAM to interact with input gaze streams alongside
the image, we trained the model partially on artificially generated gaze data. We
fine-tuned the mask decoder and prompt encoder components using synthetic gaze
point prompts. The image encoder’s parameters were unchanged and kept frozen
since the image encoder was pretrained on a large medical dataset, meaning that
it is already capable of effectively encoding medical images.
Synthetic gaze prompts were designed to replicate the eye gaze behavior of
clinicians, providing input gaze coordinates of varying length. In this configuration, the gaze data serve as an input prompt for the MedSAM’s prompt encoder,
controlling the segmentation process.
3.3.2
Gaze Prompts Generation
The gaze stream presents distinct characteristics compared to other types
of interaction, including mouse clicks or bounding boxes. Firstly, gaze stream
lacks the ability to clearly indicate which gaze points are background or foreground, meaning that it is quite challenging to detect whether the user looked
at the object to add or remove segmentation prediction. However, the MedSAM
prompt encoder necessitates that gaze points be labeled as "foreground" (label
1), "background" (label 0), or "not a point" (label -1). Determining which gaze
points to include or exclude during eye-tracking experiments poses significant
difficulties. To address this challenge within the fine-tuning pipeline, the gaze
prompts were generated carefully. Several labeling strategies for the point prompts
were proposed, including (i) randomly assigning "foreground" or "background"
labels to points, (ii) omitting a point embedding from the prompt encoder and


<!-- Page 30 -->

### 3.3 Model Training on Synthetic Gaze Data
passing gaze coordinates without any labels, and (iii) fixing the label to all points
as "foreground". During the analysis, all strategies demonstrated comparable
performance. Consequently, the approach was selected due to simplicity and
consistency in experiments.
Secondly, gaze data can suffer from imprecision. The initial idea was to
fine-tune MedSAM using coordinates randomly generated from the reference
segmentation area. However, this approach led to poor accuracy during the inference phase, particularly when some input points fell outside the organ area. This
issue likely arose because the model was trained exclusively on points located
within the ground truth mask, resulting in heightened sensitivity to areas beyond
the region of interest, which did not accurately reflect genuine eye gaze behavior.
To solve this issue, eye gaze coordinates were generated in a way that ensures a
more realistic representation of gaze behavior. Specifically, 80% of the generated
points were selected to fall within the specified organ structure, particularly within
the reference segmentation mask, while the remaining 20% were positioned outside this mask. These proportions are justified by the natural variability in gaze
behavior and the potential inaccuracies associated with eye-tracking. It was assumed that the majority of gaze points would accurately target the anatomical
structure during the segmentation process. However, the allocation of 20% of
points outside the region of interest accounted for the possibility that some gaze
points might have landed outside the desired area.
Overall, the generated gaze promptscanberepresentedasP = {[(xi, yi), 1]}N
i=1,
where N is the number of points in the gaze prompt, set as a hyperparameter. Each
point (xi, yi) represents the gaze coordinates, with 80% generated within the organ
reference segmentation mask and 20% outside the mask. The label 1 indicates
that all gaze points are denoted as "foreground".


<!-- Page 31 -->

### 3.4 Model Training on Mouse Clicks
3.4
Model Training on Mouse Clicks
In addition to the gaze-based model, we trained a model for mouse clickbased medical segmentation, which also aims to minimize the annotation effort
required from doctors. This section describes the fine-tuning procedure for the
click-based interactive method.
In this approach, the model receives the input medical image and a single
foreground point prompt, placed manually by mouse click, and generates the
segmentation mask. Similarly to the gaze-based approach stated above, we finetuned the prompt encoder and mask decoder components using synthetic point
prompts, while keeping the image encoder weights frozen.
For training, we
artificially generated synthetic point prompts by randomly sampling coordinates
from within the organ ground truth mask. Each sampled point in the prompt was
labeled as "foreground" (label 1).
3.5
Training Details
Inspired by the original MedSAM [7] and nnU-Net [20], we adopted a
composite loss function as the unweighted sum of the Dice loss (in 3.3) and the
Binary Cross-Entropy (BCE) loss (in 3.4), defined as follows:
L = LDice + LBCE.
(3.2)
We used this composite loss because it has demonstrated robustness in a
variety of segmentation tasks [20].


<!-- Page 32 -->

### 3.5 Training Details
Dice Loss.
The Dice loss, which maximizes spatial overlap between the predicted segmentation mask P and the ground truth mask G, is computed as:
LDice = 1 −
2 PN
i=1 gipi
PN
i=1(gi)2 + PN
i=1(pi)2,
(3.3)
where pi and gi denote the predicted segmentation and ground truth for voxel
i in P and G, respectively. N is the number of voxels in the image X.
Binary Cross-Entropy Loss.
The BCE loss penalizes voxel-wise prediction
errors and is defined as:
LBCE = −1
N
N
X
i=1
[gi log(pi) + (1 −gi) log(1 −pi)] ,
(3.4)
using the same notation as above.
Evaluation Metrics.
For model evaluation, we used the Dice Similarity Coefficient (DSC) as the primary metric to assess segmentation performance. The DSC
is calculated as:
DSC(G, P) = 2· | G ∩P |
| G | + | P |.
(3.5)
The DSC is used to assess the region overlap between annotation masks and
predicted masks, with its values ranging from 0 to 1.
Similarly, the Intersection over Union (IoU) is another metric used in segmentation tasks. It is defined as follows:
IoU(G, P) = | G ∩P |
| G ∪P |.
(3.6)


<!-- Page 33 -->

### 3.6 Dataset
Optimization and Training Strategy.
The AdamW [44] optimizer was employed with an initial learning rate set at 5e−5. The learning rate was reduced by 2
every 5 epochs with no improvement in validation loss. The models were trained
for 200 epochs. Additionally, we added an early stopping with a patience of 10
epochs based on validation loss and selected the last checkpoint as the final model.
Besides, the number of points in the prompt was an additional hyperparameter.
In this work, the incorporation of different numbers of points in the prompt was
evaluated, such as 20 points, 50 points, and a random number of points ranging
from 1 to 20 in the gaze prompt. For the latter approach, some point prompts were
padded with a "not a point" label (-1) during the inference and training stages.
3.6
Dataset
In this work, we used the Whole abdominal ORgan Dataset (WORD) dataset
[45] that comprises 150 CT scans collected from 150 cancer patients prior to
radiation therapy. The WORD dataset provides CT abdominal scans with manual
annotations for 16 organs, as depicted in Fig. 3.2.
Fig. 3.2. WORD dataset (Fig. 1, [45]). The left table lists the annotated organs.
In our work, we used CT images in axial views that are demonstrated in (a).


<!-- Page 34 -->

### 3.6 Dataset
Each CT scan consists of 159 to 330 slices, each with a dimension of 512 ×
512. The in-plane resolution is 0.976 mm × 0.976 mm, with slice spacing ranging
from 2.5 mm to 3.0 mm. We used training, validation and test sets that have been
originally split in [45]. For model evaluation, we used the official WORD test set.
Data Preprocessing.
We converted all CT volumes into their respective 2D
slices, each slice split to ensure that the ground truth mask corresponds to a
single distinct anatomical structure. Consequently, some organs were represented
by multiple structures when applicable. Objects smaller than 1000 pixels in 3D
or fewer than 100 pixels in 2D slices were excluded, as the primary focus is
on segmentation rather than detection. To meet network input requirements, all
images were resized to 1024×1024×3 by repeating the single channel across three
channels and the pixel values were normalized to the range [0, 1].
Table 3.1 summarizes the details and clinical characteristics of training,
validation, and test sets from the WORD after the preprocessing step. Although
the median age and sex distribution vary slightly across the training, validation,
and test splits, the differences are not critical and are unlikely to bias the outcomes.
TABLE 3.1
Characteristics for WORD dataset splits after preprocessing.
Characteristics
Training
Validation
Test
Number of scans (patients)
Number of slices
85,921
17,652
28,110
Age (median)
47 (28-75)
52 (32-78)
49 (26-72)
Male
Female
Prostatic cancer
Cervical cancer
Rectal cancer
Metastatic tumours


<!-- Page 35 -->

## Chapter 4: Experimental Setup
This chapter presents details on the experimental setup, including the emulation of a radiologist workstation equipped with eye-tracking capabilities (Section 4.1), as well as the required computational resources and software tools used
(Section 4.2).
4.1
Radiology Workstation
We developed an emulation of a radiologist workstation with eye-tracking
capabilities, as demonstrated in Fig. 4.1 and Fig. 4.2. Our setup was located in
an isolated room at our institution. The workstation incorporates a lightweight
bar-shaped eye-tracking device. The eye tracker is placed underneath the monitor.
From a hardware perspective, the workstation features an LG diagnostic monitor
with a 10-bit color depth, a resolution of 3840×2160 pixels, and a pixel density
of 7.21 px/mm. It is integrated with a Tobii Eye Tracker 4C with two Infrared
Sensor (IR) sensors, as illustrated in Fig. 4.3. This device connects to the PC
with a standard USB Type-A interface and operates at a frequency of 90 Hz.


<!-- Page 36 -->

### 4.1 Radiology Workstation
Fig. 4.1. The developed workstation with the integrated gaze-assisted segmentation system for radiologists.
Furthermore, the Tobii Eye Tracker 4C measures 17 x 15 x 335 mm, weighs
95 grams, operates at a distance of 20-37 inches, and has a tracking population
coverage of 97% 1.
In terms of precision, the Tobii Eye Tracker 4C has an
estimated spatial accuracy of less than 1.0° [46].
Before starting an experiment, each participant undergoes a calibration procedure to ensure accurate gaze tracking. Upon successful calibration, participants
interact with our custom segmentation interface. All operations in our software
are managed through several simple buttons, including Enter and Space. The
system records and synchronizes multiple data streams, including eye movement
data, segmentation predictions, and user control commands. This enables a comprehensive analysis of gaze patterns within a radiological setting.
1https://help.tobii.com/hc/en-us/articles/213414285-Specifications-for-the-Tobii-Eye-Tracker-4C


<!-- Page 37 -->

### 4.1 Radiology Workstation
Fig. 4.2. A schematic illustration of eye-tracking technology and the setup used
for our radiology workstation.
Although there is no universally standardized protocol for eye-tracking studies in radiology, we established a consistent experimental workflow to align with
the specific goals of this research. Prior to the experiments, we instructed medical
professionals on the use of our segmentation software. Comprehensive training
was conducted, which included a trial run to familiarize the doctors with the
system functionalities and control interface. The application is designed with an
intuitive menu and clear instructions to ensure ease of use from the outset.
To enhance the precision of gaze tracking, the eye tracker should be positioned directly beneath the monitor, and experiments should be carried out in a
room with controlled lighting conditions. Furthermore, the chair should be adjusted to ensure that the participant’s head is at a distance of approximately 50 cm
from the monitor for an optimal viewing experience. Additionally, recalibration


<!-- Page 38 -->

### 4.1 Radiology Workstation
Fig. 4.3. A labeled diagram of the Tobii Eye Tracker 4C model used for our
radiology workstation in experiments.
is performed whenever the participant changes position or a decrease in tracking
quality is observed.
4.1.1
Eye Calibration
To achieve optimal eye-tracking accuracy, each participant underwent a short
calibration procedure prior to a new experiment. The calibration ensures precise
tracking of eye movements and aligns eye coordinates with the participant’s focal
point. This process involved displaying a series of points on the screen, including
six calibration points. The entire procedure takes less than one minute.
The calibration process consists of two main steps: (1) verifying the participant’s head and eye positions, and (2) directing his/her eye gaze to two calibration
points near the center of the monitor and four points on the monitor, located at
the top left, top right, bottom left, and bottom right corners of the monitor.
4.1.2
Eye Tracking Software
Our developed software sequentially displays medical images and works in
three modes for different types of annotations. In the first mode, which is our
gaze-assisted approach, the software records gaze coordinates with timestamps
using the eye tracker. These gaze signals are incrementally processed by our


<!-- Page 39 -->

### 4.1 Radiology Workstation
gaze-assisted segmentation model, which operates in an iterative fashion: at each
iteration, the model reprocesses the input embedding along with the accumulated
gaze prompts to refine the segmentation mask. In the second mode, the software
accepts user input in the form of mouse clicks. These click coordinates are used to
prompt our click-based model, which generates a segmentation mask accordingly.
Similarly, in the third mode, which follows the original MedSAM approach, the
system reads the coordinates of the input bounding boxes and interacts with the
original MedSAM model.
Fig. 4.4. A diagram illustrating interface components during the organ segmentation (e.g., liver). The process includes the following steps: i) the start screen,
ii) the main screen displaying a CT slice, as well as visualizing the generated segmentation mask and gaze points (blue) at the current time, iii) the segmentation
output at the end of the procedure, showing the final segmentation mask (purple)
and the contours of the ground truth mask (dark purple).
As depicted in Fig. 4.4, GUI starts with a main screen that provides instructions on the essential control buttons and specifies the name of the target organ for
segmentation. Once started, the software displays a medical image and launches
interactive segmentation. All operations are managed through intuitive controls,
which are detailed as follows:
1. Pressing Enter displays a respective CT slice and initiates the segmentation.


<!-- Page 40 -->

### 4.2 Software and Hardware Requirements
2. Users can disable the gaze point visualizations and the predicted segmentation mask using Shift and Alt, respectively.
3. To address visibility challenges associated with the small area of certain
organs, such as the adrenal or esophagus, a zoom-in feature can be activated
by pressing Space.
4. To discard the resulting mask for the current CT slice and start segmentation
again using eye-tracking, the Backspace key is used.
5. The segmentation result is saved by pressing Enter.
The experiment settings can be managed via a configuration file, which
includes parameters, such as the frequency of updating the predicted mask in the
gaze-assisted mode, the number of gaze points to use during model inference, and
the path to the model checkpoint.
4.2
Software and Hardware Requirements
All methods and experiments were implemented using the Python programming language, leveraging a variety of libraries and frameworks, as outlined
below:
• PyTorch and PyTorch Lightning were used to implement and train deep
neural networks for image segmentation. Their built-in support for NVIDIA
CUDA-enabled GPUs significantly accelerated model training and testing.
• OpenCV, Connected Components 3D, imutils, and scikit-image libraries
were utilized for medical image analysis and processing.


<!-- Page 41 -->

### 4.2 Software and Hardware Requirements
• NumPy, pandas and os libraries were used for data processing and analysis.
• ClearML tool was employed for logging and tracking model training.
To ensure reproducibility, the versions of all the libraries used are provided
in the requirements.txt file, while detailed instructions for preparing the code
environment and running the experiments are described in the README.md file
within the project repository.
To operate the eye tracker, we highly recommend using Ubuntu version
### 18.04 LTS and the open-source installation package from the GitHub repository2.
This package includes all the necessary drivers and development libraries for
eye tracking, as well as the Tobii Pro Eye Tracker Manager, which serves as the
primary software to connect and configure the Tobii Eye Tracker 4C. The software
also provides essential functionality for device setup and eye calibration.
All of our models were trained and evaluated using the NVIDIA GTX 3090
Ti GPU. Due to resource constraints, we first fine-tuned different models on a
random sample from the WORD dataset containing almost 5% of all slices. We
then trained the best-performing approach on the whole dataset (all slices).
2https://github.com/Eitol/tobii eye tracker linux installer


<!-- Page 42 -->

## Chapter 5: Experimental Results
This chapter presents the evaluation of our gaze-assisted medical image
segmentation framework, focusing on both quantitative performance metrics and
practical usability through experiments with practicing radiologists. We divided
the experimental study into two main stages, outlined as follows:
• Stage I — Benchmarking: We evaluated the accuracy of our framework
with synthetic gaze prompts, comparing it against state-of-the-art fullyautomated medical segmentation models and interactive approaches via
bounding boxes and mouse clicks.
• Stage II — Clinical Evaluation: We conducted experiments with two
proxy radiologists and two practicing radiologists to assess both the segmentation precision and the annotation efficiency of our approaches, ultimately addressing RQs1&2. This stage includes testing various gaze point
selection strategies and comparative analysis of our gaze-assisted approach
against alternative methods, including click-based, bounding box-based interactive methods, and manual drawing tools.


<!-- Page 43 -->

### 5.1 Gaze Points Selection
Section 5.1 provides the results of various gaze point selection strategies,
addressing RQ1. Section 5.2 reports the benchmarking results using synthetic
prompts. Section 5.3 details the findings from the clinical evaluation phase, which
was conducted in close collaboration with radiologists from a public oncology
hospital, contributing to RQ2.
5.1
Gaze Points Selection
To address RQ1, we conducted a preliminary experiment involving proxy
radiologists to interact with our developed workstation and eye tracking software.
The primary goal of this experiment was to explore how to convert raw eyetracking data most effectively into input prompts for our gaze-assisted model.
Real eye gaze movements consist of rapid shifts known as saccades, followed
by fixations that occur in periods in which the eye is stationary and remains
relatively still [47]. For model inference, we used fixed-length sequences of both
fixation and random gaze points extracted from the tracking history. To retrieve
fixation points from the input gaze stream, we applied the Tobii I-VT fixation filter
algorithm1. To form the prompt of length N, sampling N random gaze points from
the gaze history can be relatively straightforward. However, fixation points can
pose additional challenges, as in some cases there may be too few fixations to
reach the desired length N. To mitigate this challenge, we designed and evaluated
two different strategies for selecting fixation points:
1. Fixations with return: we randomly select a fixation point from the available
set of fixation points multiple times, specifically, N times. This means that
some points may be selected more than once.
1Olsen, Anneli. "The Tobii I-VT fixation filter." Tobii Technology 21.4-19 (2012): 5.


<!-- Page 44 -->

### 5.1 Gaze Points Selection
2. Fixations with addition: we first select all available fixation points. Then,
we add additional points from nonfixation points to reach the total of N gaze
points required in the input prompt.
To compare gaze selection strategies and select the best-performing one, we
instructed two proxy radiologists to segment 54 organs in various slices using our
best gaze-assisted model trained on 5% of the WORD – a model with 20 points
in the prompt (refer to Appendix B for more details). Table 5.1 shows the average
Dice scores (in 3.5) for different organs using three distinct approaches. The results
indicated that selecting 20 random points from the entire gaze-tracking history,
which were sent to the model as prompts, yielded the most effective performance.
The results for the second proxy radiologist showed a similar pattern and are
provided in Appendix B, Table B.2.
TABLE 5.1
Comparison of segmentation performance (DSC (%)) across three strategies for
selecting gaze points for model inference.
Strategy
Random points
Fixations w/ return
Fixations w/ addition
Liver
96.74
62.49
94.15
Spleen
91.64
92.85
93.88
Kidney (L)
86.05
56.56
96.01
Kidney (R)
88.12
92.68
88.69
Stomach
96.85
90.69
95.07
Gallbladder
93.43
90.36
89.74
Esophagus
88.99
92.34
62.07
Pancreas
93.35
81.75
91.07
Duodenum
88.78
79.39
82.82
Colon
85.46
88.20
82.05
Intestine
83.94
79.33
77.50
Adrenal
65.00
77.30
75.45
Rectum
93.87
68.98
87.84
Bladder
39.44
16.17
72.83
Head of femur (L)
89.19
87.65
92.36
Head of femur (R)
92.32
85.85
82.86
Mean
87.03
80.79
84.42


<!-- Page 45 -->

### 5.2 Benchmarking
5.2
Benchmarking
In this section, we assess the segmentation performance of our proposed
approach and compare it with state-of-the-art segmentation models benchmarked
on the WORD dataset.
Our gaze-assisted segmentation model was trained on the entire WORD,
using a point prompt consisting of 20 points, with 80% of them located within
the ground truth mask of an anatomical structure and 20% positioned outside the
mask. This model configuration yielded the best performance among all tested
approaches, as demonstrated in Appendix B. Our click-based model was also
trained on the full WORD, with a single foreground point randomly selected from
the ground truth mask. We included MedSAM in our comparison, testing it with
bounding boxes generated using Otsu’s method based on reference masks.
TABLE 5.2
Comparison of segmentation performance (DSC (%)) with contemporary models
for abdominal organ segmentation.
Method
nnUNetV2 [20]
ResUNet [23]
MedSAM [7]
Ours (1 click)
Ours (Gaze)
Liver
### 96.19 ± 2.16
### 96.55 ± 0.89
### 92.15 ± 1.22
### 84.93 ± 3.20
### 96.00 ± 0.33
Spleen
### 94.33 ± 7.72
### 95.26 ± 2.84
### 78.68 ± 0.00
### 88.86 ± 2.04
### 96.18 ± 0.05
Kidney (L)
### 91.29 ± 18.15
### 95.63 ± 1.20
### 83.40 ± 0.00
### 93.22 ± 0.05
### 96.20 ± 0.00
Kidney (R)
### 91.20 ± 17.22
### 95.84 ± 1.16
### 91.93 ± 0.00
### 94.00 ± 0.02
### 96.35 ± 0.00
Stomach
### 91.12 ± 3.60
### 91.58 ± 2.86
### 91.61 ± 0.00
### 81.56 ± 3.34
### 95.51 ± 0.18
Gallbladder
### 83.19 ± 12.22
### 82.83 ± 11.8
### 85.43 ± 0.00
### 82.92 ± 0.30
### 92.57 ± 0.02
Esophagus
### 77.79 ± 13.51
### 77.17 ± 14.68
### 88.94 ± 5.61
### 84.35 ± 4.05
### 90.29 ± 1.23
Pancreas
### 83.55 ± 5.87
### 83.56 ± 5.60
### 79.78 ± 0.00
### 74.80 ± 1.080
### 90.85 ± 0.23
Duodenum
### 64.47 ± 15.87
### 66.67 ± 15.36
### 80.07 ± 0.00
### 70.95 ± 3.01
### 89.82 ± 0.51
Colon
### 83.92 ± 8.45
### 83.57 ± 8.69
### 75.96 ± 0.00
### 76.90 ± 9.69
### 91.80 ± 1.13
Intestine
### 86.83 ± 4.02
### 86.76 ± 3.56
### 84.00 ± 0.00
### 70.58 ± 12.94
### 90.78 ± 1.87
Adrenal
### 70.0 ± 11.86
### 70.9 ± 10.12
### 62.74 ± 5.28
### 69.00 ± 3.48
### 84.77 ± 0.77
Rectum
### 81.49 ± 7.37
### 82.16 ± 6.73
### 92.54 ± 2.33
### 85.90 ± 2.52
### 92.53 ± 0.27
Bladder
### 90.15 ± 16.85
### 91.0 ± 13.5
### 86.74 ± 0.00
### 86.42 ± 4.00
### 95.26 ± 0.02
H. femur (L)
### 93.28 ± 5.12
### 93.39 ± 5.11
### 70.17 ± 0.00
### 91.67 ± 1.88
### 94.99 ± 0.30
H. femur (R)
### 93.93 ± 4.29
### 93.88 ± 4.30
### 63.28 ± 0.00
### 91.53 ± 1.97
### 95.13 ± 0.29
Mean
### 85.80 ± 5.27
### 86.67 ± 4.81
### 81.71 ± 9.39
### 79.53 ± 18.30
### 92.53 ± 3.24


<!-- Page 46 -->

### 5.2 Benchmarking
According to Table 5.2, our model consistently outperforms both the original MedSAM through bounding boxes and mouse clicks and other state-of-the-art
2D models across various abdominal organs.
Furthermore, our gaze-assisted
approach shows significant improvements in segmentation performance (DSC),
particularly in challenging cases involving the duodenum and adrenal glands.
For instance, our segmentation model demonstrates a +14% DSC improvement
compared to nnUnetV2 [20] for the adrenal organ. Fig. 5.1 illustrates this comparison, highlighting the consistent advantage of our gaze-based model, specifically
in complex organs, e.g., intestine, colon, or small anatomical structures, e.g.,
adrenal and gallbladder.
Liver
Spleen
Kidney (L)
Kidney (R)
Stomach
Gallbladder
Esophagus
Pancreas
Duodenum
Colon
Intestine
Adrenal
Rectum
Bladder
Head of femur (L)
Head of femur (R)
nnUNetV2
ResUNet
MedSAM (Bbox)
Ours (1 click)
Ours (Gaze)
Fig. 5.1.
Visualization of segmentation performance comparison (DSC (%))
between different methods across abdominal organs.


<!-- Page 47 -->

### 5.3 Clinical Evaluation
5.3
Clinical Evaluation
Four medical experts, including two proxy radiologists and two practicing
radiologists, were recruited to participate in our experiments (see Fig. 5.2).
Fig. 5.2. One of participating radiologists uses our gaze-assisted system to analyze
the abdominal CT slice and perform segmentation.
Radiologist A specializes in classical radiography and CT having five years
of professional experience, while Radiologist B has eight years of expertise in
classical diagnostics, CT, and MRI, with a focus on oncology and differential
diagnosis of malignant processes. Participating medical experts used our approach
to segment organs on CT slices independently, without collaborative discussion.
The time taken for each case during the experiments was recorded.
Fig. 5.3
provides visualization examples of segmentation predictions made based on the
eye gaze of the medical expert during our experiments.


<!-- Page 48 -->

### 5.3 Clinical Evaluation
(a) Initial predicted mask.
(b) Mask by half correction.
(c) Mask by full correction.
(d) Initial predicted mask.
(e) Mask by half correction.
(f) Mask by full correction.
Fig. 5.3. Steps to correct segmentation masks for abdominal organs, such as the
spleen and left kidney, on different CT slices. Each subfigure shows the outline of
reference segmentation contours (dark purple), the predicted segmentation mask
(purple), and gaze points (blue) passed to our gaze-based model.
5.3.1
Comparison with Existing Tools
To investigate RQ2, we conducted experiments with two proxy radiologists.
Initially, the experts manually segmented a dataset of 160 CT slices using a
standard drawing tool, MedSAM with bounding boxes and mouse clicks. The
dataset included images from two patients, with five slices per organ, sourced
from the test set of WORD. The radiologists then segmented this dataset using
our gaze-assisted segmentation system, which tracks eye gaze movements, selects
20 random gaze points at each iteration, and uses these as the prompt for our
model to generate segmentation.


<!-- Page 49 -->

### 5.3 Clinical Evaluation
Tables 5.3 and 5.4 present a comparison of interactive approaches, such
as manual drawing, MedSAM with bounding boxes (bboxes), and our proposed
methods with mouse clicks and gaze.
According to Table 5.3, segmentation using our gaze-based system is approximately twice as fast as MedSAM with bboxes and 3.3 times faster than manual
annotation. In terms of segmentation performance, our gaze-assisted method
achieved competitive performance, reaching a mean Dice of 90.5% across 16
abdominal organs, closely matching MedSAM (90.9%) and drawing (91.9%).
While our click-based approach achieved the highest efficiency with a mean time
of 1.6 seconds per image, it demonstrated lower accuracy (86.5% DSC).
TABLE 5.3
Comparison of mean segmentation performance (DSC (%)) and efficiency (time
per image in seconds) in the experiment with the first radiologist.
Manual drawing
MedSAM (Bboxes)
Ours (1 click)
Ours (Gaze)
DSC, %
91.9
90.9
86.5
90.5
Time, s
18.6
10.8
1.6
5.7
The results provided in Table 5.4 indicate that our gaze-based approach
achieved the highest accuracy (92.9% DSC), surpassing both manual drawing
(91.5% DSC) and MedSAM with bounding boxes (90.5% DSC). In terms of
efficiency, our gaze-assisted method performed almost 2 times faster than manual
drawing and slightly faster than MedSAM via bounding boxes.
TABLE 5.4
Comparison of mean segmentation performance (DSC (%)) and efficiency (time
per image in seconds) in the experiment with the second radiologist.
Manual drawing
MedSAM (Bboxes)
Ours (1 click)
Ours (Gaze)
DSC, %
91.5
90.5
87.7
92.9
Time, s
20.1
13.1
3.2
10.1


<!-- Page 50 -->

### 5.3 Clinical Evaluation
Manual drawing
MedSAM (Bboxes)
Ours (1 click)
Ours (Gaze)
80.0
82.5
85.0
87.5
90.0
92.5
95.0
97.5
100.0
DSC (%)
91.9
91.5
90.9
90.5
86.5
87.7
90.5
92.9
Radiologist 1
Radiologist 2
(a) Mean segmentation accuracy in DSC (↑).
Manual drawing
MedSAM (Bboxes)
Ours (1 click)
Ours (Gaze)
Time (s)
18.6
20.1
10.8
13.1
1.6
3.2
5.7
10.1
Radiologist 1
Radiologist 2
(b) Mean time per image in seconds (↓).
Fig. 5.4. Comparison of segmentation accuracy and efficiency across annotation
tools: manual drawing, MedSAM with bounding boxes, our method with a single
mouse click, and our gaze-assisted method.
Results are averaged across 16
abdominal organs and evaluated by two proxy radiologists.
Overall, the proposed gaze-assisted approach strikes a balance between segmentation performance and annotation speed, as demonstrated in Fig. 5.4. Our
gaze-assisted method can offer a practical and effective alternative to both the
manual tool and MedSAM with bounding boxes and mouse clicks. While the
mouse-click approach is notably faster in both runs of the experiment, its lower
segmentation accuracy makes it less suitable for the high precision required in
such high-risk domains, such as medicine.
5.3.2
Segmentation Correction Using Gaze
For this part of our study, we selected 100 CT slices from the test set of the
WORD dataset, which involved 20 patients. We chose five CT slices per patient,
ensuring that each image represented a different organ. The dataset maintained a
balanced organ distribution, with most organs represented by 7 samples, while the
spleen, right kidney, and stomach had 3 samples each. Moreover, data selection


<!-- Page 51 -->

### 5.3 Clinical Evaluation
was based on the segmentation performance of MedSAM predictions made using
synthetic bounding boxes. The bounding boxes were artificially generated using
Otsu’s technique. More specifically, we chose 60 samples with low performance
(DSC less than 70%) and 40 samples with high DSC values (DSC higher than
70%). As a result, samples selected for the experiments primarily include challenging cases for traditional methods, particularly those based on bounding boxes.
These CT images were presented as experimental images to Radiologists A and B,
with the order of the images inverted to mitigate any potential biases in the final
assessment. Both medical professionals were tasked with constructing bounding
boxes to segment each organ using the original MedSAM. When the segmentation
results were inaccurate, radiologists refined the segmentation with the assistance
of our gaze-assisted approach.
Pancreas
Colon
Intestine
Adrenal
Femur (L)
Femur (R)
DSC (%)
55.5
50.9
62.0
89.8
+28%
49.7
62.8
+13%
43.2
66.6
+23%
14.9
54.1
+39%
24.4
58.7
+34%
Bboxes
Eye Gaze
Fig. 5.5. Segmentation performance (DSC (%)) comparison after correction with
gaze in experiment with Radiologist A.
As can be seen from Fig. 5.5, Radiologist A corrected 6 organs, including
the pancreas, colon, intestine, adrenal, and left and right heads of femur, with 11


<!-- Page 52 -->

### 5.3 Clinical Evaluation
segmentation masks from 9 different patients. The bounding box method demonstrated a mean Dice coefficient of 39% with an average time of 9.7 seconds.
After applying corrections based on eye gaze, the segmentation performance improved significantly (+24% in average DSC), although the average time increased
to approximately 15.7 seconds, as provided in Table 5.5. The remaining 89 organs, which did not require any corrections using gaze-assisted approach, were
segmented using the original MedSAM method with manually created bounding
boxes, accounting to a mean Dice score of 70.48%.
TABLE 5.5
Results of the mask correction using eye gaze for the first doctor.
Bboxes
Eye gaze
Organ
DSC, %
Time, s
DSC, %
Time, s
Pancreas
55.46
3.14
50.94
5.02
Colon
62.04
22.16
89.75
23.64
Intestine
49.73
20.69
62.79
24.55
Adrenal
43.21
4.55
66.56
14.19
Head of femur (L)
14.89
9.67
54.12
7.68
Head of femur (R)
24.45
6.07
58.73
19.42
Mean
39.04
9.7
63.18
15.7
TABLE 5.6
Results of the mask correction using eye gaze for the second doctor.
Bboxes
Eye gaze
Organ
DSC, %
Time, s
DSC, %
Time, s
Liver
57.74
6.68
60.95
17.68
Esophagus
68.55
7.76
75.25
12.56
Duodenum
66.95
8.66
75.04
41.01
Colon
57.38
9.49
66.87
58.43
Intestine
52.68
26.94
76.72
65.99
Rectum
85.37
7.28
66.69
24.03
Bladder
55.68
8.86
57.85
42.79
Mean
61.70
13.58
71.57
41.79


<!-- Page 53 -->

### 5.3 Clinical Evaluation
According to Table 5.6, the bounding box-based method showed a mean
Dice of 61.7% with an average time of approximately 13.5 seconds. After eye
gaze correction, the mean Dice score increased to 71.57%, while the average time
extended to almost 42 seconds. Radiologist B corrected 14 masks from 9 patients
across 7 organs using eye tracking (refer to Fig. 5.6). The organs were the liver,
esophagus, duodenum, colon, intestine, rectum, and bladder. For the remaining
86 organs requiring no corrections, the bounding box method demonstrated a
Dice coefficient of 71.39%.
Liver
Esophagus
Duodenum
Colon
Intestine
Rectum
Bladder
DSC (%)
57.7
61.0
68.5
75.2
+7%
67.0
75.0
+8%
57.4
66.9
+9%
52.7
76.7
+24%
85.4
66.7
55.7
57.9
Bboxes
Eye Gaze
Fig. 5.6. Segmentation performance (DSC (%)) comparison after correction using
gaze-assisted model in the experiment with Radiologist B.
Interestingly, following the conducted experiments, we observed the same
distribution of eye gaze as in our training setup (80% inside and 20% outside the
reference mask) of Radiologist A, confirming our assumption for generating gaze
point prompts used for model training.


<!-- Page 54 -->

## Chapter 6: Discussion
This chapter discusses the implications of our findings, starting with Section 6.1 that presents a detailed organ-level analysis of segmentation performance
and identifies patterns and challenges across various anatomical structures. Section 6.2 describes the validation of segmentation outcomes by an invited senior
radiologist, focusing on the interpretability of the results and their clinical relevance. Section 6.3 reflects on the broader potential of our approach in clinical
settings, followed by Section 6.4, which outlines limitations and proposes future
directions. Finally, Section 6.5 addresses the ethical considerations surrounding
the integration of eye-tracking technology into radiological workflows.
Overall, our gaze-assisted approach outperformed interactive approaches,
including bounding boxes and mouse clicks, interms ofsegmentationperformance
and improved the efficiency of some existing approaches, such as drawing tool.
Furthermore, our gaze-assisted model enhanced segmentation performance for
challenging organ views. For instance, for Radiologist A, the mean Dice score
increased by almost 1.5 times after the correction using eye gaze.
However,
the time needed to complete the segmentation task was extended, highlighting a


<!-- Page 55 -->

### 6.1 Organ-Level Segmentation Analysis
trade-off between accuracy and efficiency. Nevertheless, the critical importance
of accuracy in medical diagnosis, particularly in oncology treatment planning,
underscores the value of our approach. Furthermore, although the initial guidance
for medical professionals using the eye tracker was brief in our experiments, there
is room for improved training on its effective use. As integration of eye-tracking
technology becomes more commonly used in medical practice, it is likely to
further enhance efficiency over time.
6.1
Organ-Level Segmentation Analysis
In our analysis, certain organs, such as the spleen, stomach, gallbladder,
esophagus, and kidneys, demonstrated a high quality of segmentation by bounding
boxes, requiring no additional correction efforts. For instance, the bounding box
constructed for the spleen often aligned well with its anatomical boundaries,
resulting in a relatively low average segmentation error of only 12%, as presented
in Table 6.1.
Similarly, segmentation of the left and right kidneys using the
MedSAM bounding box-based approach showed high quality, with average Dice
scores of 78.4% and 86.9%, respectively.
The bladder organ was also wellsegmented with the use of bounding boxes, demonstrating an average Dice value
of 77.8%. However, the segmentation performance for the bladder by Radiologist
B appeared to be low, with a mean DSC of 57.9% after correction using eye gaze, as
its small area can pose challenges in some cases, as mentioned in [48]. In contrast,
the liver, despite being a large and easily identifiable organ [48], can present
challenges due to the difficulty in distinguishing its boundaries from surrounding
anatomical structures [20]. The average Dice score for liver segmentation based
on bounding boxes accounted for 62.7%, demonstrating the need for correction.


<!-- Page 56 -->

### 6.1 Organ-Level Segmentation Analysis
Nevertheless, the pancreas, which has a quite small size, demonstrated lower
accuracy, with an average DSC of 53.4%.
Recent studies highlight that the
pancreas’s small and irregular shape can lead to possible errors in segmentation
[45], [49], necessitating correction efforts. Furthermore, smaller organs, such
as the duodenum, gallbladder, pancreas, and rectum, consistently showed lower
segmentation performance across various state-of-the-art models [20], [23].
TABLE 6.1
The mean DSC (%) and average time in seconds for segmentation using only
bounding boxes (before or without corrections using the eye tracker) for both
Radiologists A and B.
Organ
DSC, %
Time, s
Liver
62.70
2.66
Spleen
88.22
2.36
Kidney (L)
78.35
1.48
Kidney (R)
86.92
1.57
Stomach
86.83
0.02
Gallbladder
73.06
2.15
Esophagus
59.69
4.00
Pancreas
53.45
4.37
Duodenum
70.93
5.33
Colon
68.45
7.42
Intestine
52.84
20.21
Adrenal
51.40
3.41
Rectum
64.76
5.96
Bladder
77.77
2.82
Head of Femur (L)
36.91
7.24
Head of Femur (R)
36.55
9.51
Mean
64.02
5.50
Larger organs, including the liver, spleen, kidneys, stomach, and bladder,
displayed promising segmentation results, with average Dice scores reflecting
strong performance and requiring minimal correction efforts, as demonstrated
in Table 5.2 and supported by previous studies in the relevant literature [45].


<!-- Page 57 -->

### 6.2 Medical Expert Validation
However, certain structures, such as the left and right heads of the femur, with
Dice scores of 36.9% and 36.6%, respectively, showed considerable inaccuracies
with MedSAM, likely due to the large bone structures and complex geometry
[48] requiring further refinement in segmentation. In response, Radiologist A
corrected the initial prediction and applied our gaze-assisted approach, increasing
the mean Dice scores from 14.9% to 54.1% and from 24.5% to 58.7%, respectively.
Overall, while many organs demonstrated effective segmentation results, certain
areas necessitated correction and refinement to enhance quality.
Besides, we examined correlations between the parameters of our experiments. First, we identified a positive correlation between the time required to
segment an organ in an image and the size of the organ, with a Pearson Correlation Coefficient (PCC) of 0.67. This relationship is intuitive, as larger organs
typically demand more attention, leading to greater variance in gaze movements.
Consequently, more time is required for the segmentation, as the annotator may
need to analyze multiple structures of the single organ. Furthermore, despite the
increased time needed for segmentation of larger organs, they are often segmented
more accurately, which aligns with the relevant literature [45].
6.2
Medical Expert Validation
We presented the results of the experiment on segmentation correction using
gaze to a Medical Expert. He is a Doctor of Medical Sciences, Professor of the
Department of Radiation Diagnostics, and Head of the Department of Radiation
Diagnostics of the Clinical Oncology Dispensary (Kazan, Tatarstan) with 23 years
of professional experience. Based on the Expert’s feedback, we selected several
interesting cases that could be valuable for analysis.


<!-- Page 58 -->

### 6.2 Medical Expert Validation
(a) Bounding box defined by the doctor.
(b) Ground truth and prediction using bbox.
Fig. 6.1. Segmentation results for the adrenal gland, which are revised by the
Medical Expert. The bounding box (blue), final segmentation mask generated
based on this bounding box (blue), and the contours of the ground truth mask
(dark purple) are shown.
The case illustrated in Fig. 6.1 focuses on the prediction of the left adrenal
gland using MedSAM bounding boxes made by Radiologist A. Although Radiologist A determined that gaze-assisted corrections were unnecessary, the error
associated with the bounding box approach was significant, amounting to 53%.
This error can be explained by the varying opinions within the expert community.
Although Medical Expert reported the final predicted segmentation mask to be
accurate, the annotation of the adrenal organ was criticized for its lack of precision, as it also included the aorta, which is a redundant part for this case. This
disagreement reveals a broader challenge: accuracy can be influenced by differing expert interpretations, and even datasets like WORD may carry annotation
inconsistencies. Such cases emphasize the importance of expert validation.
Let us consider another representative patient case involving the pancreas
segmentation, demonstrated in Fig. 6.2. Despite a visually minor error in the bbox-


<!-- Page 59 -->

### 6.2 Medical Expert Validation
(a) Ground truth and prediction using bbox.
(b) Ground truth and prediction using gaze.
Fig. 6.2. Segmentation predictions for the pancreas organ generated using approaches based on bounding boxes (blue) and eye gaze (purple) derived by participated doctor. The ground truth mask is shown using contours (dark purple).
based segmentation, one of the participating radiologists proceeded to refine the
segmentation mask using gaze-based corrections. However, upon expert review,
the Medical Expert identified this error as clinically significant, as the organ in
this slice constituted a small area. The Expert also noted the inaccuracy of the
segmentation mask predicted based on eye gaze, indicating that segmentation of
smaller organs remains more challenging than that of larger ones.
Finally, in Fig. 6.3, we show another case involving the segmentation of the
duodenum organ. Using the initial bounding box approach, the segmentation
resulted in a DSC of 63% (refer to Fig. 6.3a). Following gaze-assisted correction,
the radiologist substantially improved the segmentation quality to approximately
80% (+17% DSC, Fig. 6.3b). The Medical Expert confirmed that the segmentation mask obtained after gaze correction was accurate and clinically reliable.
Conversely, the initial segmentation mask derived from the bounding box method
was deemed inaccurate, since it incorrectly included the inferior vena cava. In cer-


<!-- Page 60 -->

### 6.3 Clinical Practice
(a) Ground truth and prediction using bbox.
(b) Ground truth and prediction using gaze.
Fig. 6.3. Segmentation masks for the duodenum organ generated using MedSAM
with bounding boxes (blue) and our gaze-assisted tool (purple) in radiologists’
experiments, which are checked by the Medical Expert. The reference mask for
the duodenum is shown using contours (dark purple).
tain cases, when the shape of an organ in a slice resembles a non-convex geometric
figure, the bounding box-based method can lead to inaccuracies in delineating the
organ, as the bounding box may also capture redundant surrounding structures for
the organ. Importantly, this problem can be solved using gaze correction.
6.3
Clinical Practice
While similar studies have demonstrated improved diagnostic accuracy compared to the original MedSAM model, this research is the first to focus on enhancing medical image segmentation through eye-tracking techniques. Furthermore,
this work involved thorough experiments in close collaboration with medical professionals from the oncology hospital, ensuring a valid evaluation of the proposed
approach and its potential for clinical use.


<!-- Page 61 -->

### 6.4 Limitations and Future Work
Our developed setup mimics the clinical environment, where the medical
expert interacts with the system while the eye-tracking device seamlessly records
gaze behavior. The collected gaze data is then utilized to perform the segmentation
process in real-time. As such, this system could feasibly be integrated into clinical
practice with minimal disruption to existing workflows, offering a promising
direction for semi-automated, human-in-the-loop AI tools in medicine.
6.4
Limitations and Future Work
This work has several limitations. First, we used only one dataset, in particular, focused in abdominal CT imaging. The findings are currently scoped to
this anatomical region and imaging modality. Therefore, future research should
incorporate additional datasets and explore other modalities beyond the abdominal one. Second, the current implementation and evaluation with clinicians were
based on two-dimensional image slices. While our solution simplifies the user
interaction and saves time needed for model inference, it does not reflect the
full complexity of clinical workflows, which often require segmentation across
multiple contiguous slices or in full three-dimensional volumes. Future research
should prioritize the use of volumetric medical data with the ability to manipulate
and navigate across multiple slices. Third, participating radiologists received only
brief instruction in using the eye-tracking tool before experiments. This may have
influenced both accuracy and speed. Further research should assess the impact
of training duration, user familiarity, and inter-user variability on segmentation
performance.
Finally, while this study focused on the development of mouse-click and gazebased interactions, future research could explore hybrid approaches that combine


<!-- Page 62 -->

### 6.5 Ethical Statement
automated segmentation tools with interactive correction. Such integration may
enhance clinical utility by enabling experts to efficiently refine automated outputs
when necessary.
6.5
Ethical Statement
This work has significant societal potential by proposing a novel way for
speeding up radiological processes in a safe manner, where AI is not used to make
clinical decisions but directly assists radiologists in medical image analysis in a
straightforward and transparent manner.
In the real-world setting, the system can be deployed so that the eye tracker
passively captures gaze data while the radiologist works. This recorded gaze data
can be used in real time to assist segmentation and support decision-making but it
does not need to be stored or recorded permanently, thereby preserving clinician
privacy and data security. All involved medical professionals should be fully
informed about how gaze data is used and assured that no personally identifiable
or biometric information is retained beyond the session.


<!-- Page 63 -->

## Chapter 7: Conclusion
The task of medical image segmentation has consistently presented challenges, indicating significant opportunities for enhancement.
We presented a
novel gaze-assisted approach for interactive segmentation of medical images,
built on MedSAM foundation model. By leveraging eye gaze coordinates as point
prompts, our method offers a more intuitive solution for medical image annotation
and achieves state-of-the-art performance, particularly in abdominal CT imaging
– a domain where precise segmentation is essential for radiotherapy and cancer
treatment planning.
One of the key contributions of this research lies in the development of an
interactive system for analyzing medical images using eye-tracking technology.
Our system enables real-time corrections to segmentation masks by incorporating
gaze data, dramatically reducing the effort required for medical annotation – a
manual task that is often time-consuming and prone to errors.
The experiments, conducted in close collaboration with clinical experts,
demonstrated the effectiveness oftheproposedgaze-assistedsegmentationmethod.
First, we demonstrated that gaze data can be successfully used in a form of point


<!-- Page 64 -->

prompts to guide the MedSAM model in medical image segmentation, particularly for abdominal organ segmentation.
Second, the gaze-assisted method
outperformed the baseline MedSAM model with bounding boxes, achieving an
almost 11% improvement in segmentation accuracy. In real-time applications,
our method not only provided approximately 1–2% improvement in precision but
also significantly reduced annotation time, taking less than half the time compared
to methods based on bounding boxes and mouse clicks.
The main findings of this research can be summarized as follows: (1) development of a model for interactive medical segmentation using a mouse click,
(2) development of a gaze-assisted medical segmentation model leveraging realtime eye movements, (3) superior performance of gaze-assisted segmentation in
abdominal CT imaging tasks, and (4) substantial improvements in segmentation
quality through gaze-based interaction. Despite these advancements, we acknowledge several limitations. The reliance on specialized hardware for gaze tracking
may restrict accessibility in some clinical settings.
Additionally, our current
gaze-assisted model is primarily trained on abdominal CT images, which opens
the door for future research to explore its applicability and effectiveness across
other medical imaging modalities.
This study contributes to the growing body of research in human-AI interaction in medicine, highlighting the potential of gaze guidance to improve diagnostic
processes. It opens avenues for further exploration of interactive segmentation
using eye gaze, which can enhance clinical workflows.


<!-- Page 65 -->

Acknowledgement
I would like to express my gratitude to the Medical AI Lab for providing the
computational resources necessary for this research. I am especially thankful to
my co-authors and colleagues at the lab, including my external supervisor, Bulat
Ibragimov, and my work supervisors, Ilya Pershin and Ramil Kuleev, for their
support, guidance, and collaboration. I am truly grateful for the opportunity to
work with them.
I would like to extend my gratitude to my thesis supervisor, Rustam Lukmanov, for his continuous help and support throughout this year. His feedback
and advice have been immensely helpful.
Moreover, I would like to thank the Video Content Department of Innopolis
University for their creativity and assistance in filming the demonstration video.
Finally, I am deeply grateful to my family for their unconditional support,
love, and belief in me.


<!-- Page 66 -->

## Bibliography
[1]
C. D. Lantsman, Y. Barash, E. Klang, L. Guranda, E. Konen, and N.
Tau, “Trend in radiologist workload compared to number of admissions
in the emergency department,” European Journal of Radiology, vol. 149,
p. 110 195, 2022.
[2]
R. Bruls and R. Kwee, “Workload for radiologists during on-call hours:
Dramatic increase in the past 15 years,” Insights into imaging, vol. 11,
pp. 1–7, 2020.
[3]
R. Alexander, S. Waite, M. A. Bruno, et al., “Mandating limits on workload,
duty, and speed in radiology,” Radiology, vol. 304, no. 2, pp. 274–282,
2022.
[4]
X. Chen, S. Sun, N. Bai, et al., “A deep learning-based auto-segmentation
system for organs-at-risk on whole-body computed tomography images for
radiation therapy,” Radiotherapy and Oncology, vol. 160, pp. 175–184,
2021.
[5]
N. Sharma and L. M. Aggarwal, “Automated medical image segmentation
techniques,” Journal of medical physics, vol. 35, no. 1, pp. 3–14, 2010.


<!-- Page 67 -->

BIBLIOGRAPHY
[6]
H. Fu, J. Zhang, B. Li, et al., “Abdominal multi-organ segmentation in
multi-sequence mris based on visual attention guided network and knowledge distillation,” Physica Medica, vol. 122, p. 103 385, 2024.
[7]
J. Ma, Y. He, F. Li, L. Han, C. You, and B. Wang, “Segment anything in
medical images,” Nature Communications, vol. 15, no. 1, p. 654, 2024.
[8]
Z. Tian, C. Shen, X. Wang, and H. Chen, “Boxinst: High-performance instance segmentation with boxannotations,”in ProceedingsoftheIEEE/CVF
Conference on Computer Vision and Pattern Recognition, 2021, pp. 5443–
5452.
[9]
K. Sofiiuk, I. A. Petrov, and A. Konushin, “Reviving iterative training with
mask guidance for interactive segmentation,” in 2022 IEEE International
Conference on Image Processing (ICIP), IEEE, 2022, pp. 3141–3145.
[10]
B. Cheng, O. Parkhi, and A. Kirillov, “Pointly-supervised instance segmentation,” in Proceedings of the IEEE/CVF Conference on Computer Vision
and Pattern Recognition, 2022, pp. 2617–2626.
[11]
H. E. Wong, M. Rakic, J. Guttag, and A. V. Dalca, “Scribbleprompt: Fastand
flexible interactive segmentation for any biomedical image,” in European
Conference on Computer Vision, Springer, 2024, pp. 207–229.
[12]
B. Wang, A. Aboah, Z. Zhang, H. Pan, and U. Bagci, “Gazesam: Interactive image segmentation with eye gaze and segment anything model,” in
NeuRIPS 2023 Workshop on Gaze Meets ML, 2023. [Online]. Available:
https://openreview.net/forum?id=hJ5DREWdjs.
[13]
L. Khaertdinova, T. Shmykova, I. Pershin, et al., “Gaze assistance for
efficient segmentation correction of medical images,” IEEE Access, 2025.


<!-- Page 68 -->

BIBLIOGRAPHY
[14]
L. Khaertdinova, I. Pershin, T. Shmykova, and B. Ibragimov, “Gaze-assisted
medical image segmentation,” arXiv preprint arXiv:2410.17920, 2024.
[15]
S. Minaee, Y. Boykov, F. Porikli, A. Plaza, N. Kehtarnavaz, and D. Terzopoulos, “Image segmentation using deep learning: A survey,” IEEE
transactions on pattern analysis and machine intelligence, vol. 44, no. 7,
pp. 3523–3542, 2021.
[16]
A. Parvaiz, M. A. Khalid, R. Zafar, H. Ameer, M. Ali, and M. M. Fraz,
“Vision transformers in medical computer vision—a contemplative retrospection,” Engineering Applications of Artificial Intelligence, vol. 122,
p. 106 126, 2023.
[17]
L. Huang, S. Ruan, and T. Denœux, “Application of belief functions to medical image segmentation: A review,” Information fusion, vol. 91, pp. 737–
756, 2023.
[18]
H. Tang, X. Chen, Y. Liu, et al., “Clinically applicable deep learning
framework for organs at risk delineation in ct images,” Nature Machine
Intelligence, vol. 1, no. 10, pp. 480–491, 2019.
[19]
O. Ronneberger, P. Fischer, and T. Brox, “U-net: Convolutional networks
for biomedical image segmentation,” in Medical image computing and
computer-assisted intervention–MICCAI 2015: 18th international conference, Munich, Germany, October 5-9, 2015, proceedings, part III 18,
Springer, 2015, pp. 234–241.
[20]
F. Isensee, P. F. Jaeger, S. A. Kohl, J. Petersen, and K. H. Maier-Hein,
“Nnu-net: A self-configuring method for deep learning-based biomedical
image segmentation,” Nature methods, vol. 18, no. 2, pp. 203–211, 2021.


<!-- Page 69 -->

BIBLIOGRAPHY
[21]
¨O. ¸Ci¸cek, A. Abdulkadir, S. S. Lienkamp, T. Brox, and O. Ronneberger, “3d
u-net: Learning dense volumetric segmentation from sparse annotation,” in
Medical Image Computing and Computer-Assisted Intervention–MICCAI
2016: 19th International Conference, Athens, Greece, October 17-21, 2016,
Proceedings, Part II 19, Springer, 2016, pp. 424–432.
[22]
X. Xiao, S. Lian, Z. Luo, and S. Li, “Weighted res-unet for high-quality
retina vessel segmentation,” in 2018 9th international conference on information technology in medicine and education (ITME), IEEE, 2018, pp. 327–
331.
[23]
F. I. Diakogiannis, F. Waldner, P. Caccetta, and C. Wu, “Resunet-a: A deep
learning framework for semantic segmentation of remotely sensed data,”
ISPRS Journal of Photogrammetry and Remote Sensing, vol. 162, pp. 94–
114, 2020.
[24]
Z. Zhou, M. M. Rahman Siddiquee, N. Tajbakhsh, and J. Liang, “Unet++:
A nested u-net architecture for medical image segmentation,” in Deep
learning in medical image analysis and multimodal learning for clinical
decision support: 4th international workshop, DLMIA 2018, and 8th international workshop, ML-CDS 2018, held in conjunction with MICCAI 2018,
Granada, Spain, September 20, 2018, proceedings 4, Springer, 2018, pp. 3–
11.
[25]
O. Oktay, J. Schlemper, L. L. Folgoc, et al., “Attention u-net: Learning
where to look for the pancreas,” arXiv preprint arXiv:1804.03999, 2018.
[26]
L.-C. Chen, Y. Zhu, G. Papandreou, F. Schroff, and H. Adam, “Encoderdecoder with atrous separable convolution for semantic image segmen-


<!-- Page 70 -->

BIBLIOGRAPHY
tation,” in Proceedings of the European conference on computer vision
(ECCV), 2018, pp. 801–818.
[27]
R. Azad, M. Heidari, M. Shariatnia, et al., “Transdeeplab: Convolutionfree transformer-based deeplab v3+ for medical image segmentation,” in
International Workshop on PRedictive Intelligence In MEdicine, Springer,
2022, pp. 91–102.
[28]
J. Chen, Y. Lu, Q. Yu, et al., “Transunet: Transformers make strong encoders
for medical image segmentation,” arXiv preprint arXiv:2102.04306, 2021.
[29]
H.-Y. Zhou, J. Guo, Y. Zhang, L. Yu, L. Wang, and Y. Yu, “Nnformer: Interleaved transformer for volumetricsegmentation,” arXivpreprintarXiv:2109.03201,
2021.
[30]
A. Hatamizadeh, Y. Tang, V. Nath, et al., “Unetr: Transformers for 3d
medical image segmentation,” in Proceedings of the IEEE/CVF winter
conference on applications of computer vision, 2022, pp. 574–584.
[31]
A. Hatamizadeh, V. Nath, Y. Tang, D. Yang, H. R. Roth, and D. Xu, “Swin
unetr: Swin transformers for semantic segmentation of brain tumors in mri
images,” in International MICCAI brainlesion workshop, Springer, 2021,
pp. 272–284.
[32]
J. Ma, F. Li, and B. Wang, “U-mamba: Enhancing long-range dependency
for biomedical image segmentation,” arXiv preprint arXiv:2401.04722,
2024.
[33]
Y. Boykov and M.-P. Jolly, “Interactive graph cuts for optimal boundary
& region segmentation of objects in n-d images,” in Proceedings Eighth


<!-- Page 71 -->

BIBLIOGRAPHY
IEEE International Conference on Computer Vision. ICCV 2001, vol. 1,
2001, 105–112 vol.1. DOI: 10.1109/ICCV.2001.937505.
[34]
L. Grady, “Random walks for image segmentation,” IEEE Transactions on
Pattern Analysis and Machine Intelligence, vol. 28, no. 11, pp. 1768–1783,
2006. DOI: 10.1109/TPAMI.2006.233.
[35]
A. Kirillov, E. Mintun, N. Ravi, et al., “Segment anything,” in Proceedings
of the IEEE/CVF International Conference on Computer Vision, 2023,
pp. 4015–4026.
[36]
D. Acuna, H. Ling, A. Kar, and S. Fidler, “Efficient interactive annotation
of segmentation datasets with polygon-rnn++,” in Proceedings of the IEEE
conference on Computer Vision and Pattern Recognition, 2018, pp. 859–
868.
[37]
S. P. Singh, L. Wang, S. Gupta, H. Goli, P. Padmanabhan, and B. Guly´as,
“3d deep learning on medical images: A review,” Sensors, vol. 20, no. 18,
p. 5097, 2020.
[38]
J. Wang, L. Wei, L. Wang, Q. Zhou, L. Zhu, and J. Qin, “Boundary-aware
transformers for skin lesion segmentation,” in Medical image computing
and computer assisted intervention–mICCAI 2021: 24th international conference, Strasbourg, France, September 27–October 1, 2021, proceedings,
part i 24, Springer, 2021, pp. 206–216.
[39]
S. Osher, N. Paragios, and R. Kimmel, Fast edge integration, 2003.
[40]
K. J. Batenburg and J. Sijbers, “Adaptive thresholding of tomograms by
projection distance minimization,” Pattern Recognition, vol. 42, no. 10,
pp. 2297–2305, 2009.


<!-- Page 72 -->

BIBLIOGRAPHY
[41]
D. Onoma, S. Ruan, S. Thureau, et al., “Segmentation of heterogeneous or
small fdg pet positive tissue based on a 3d-locally adaptive random walk
algorithm,” Computerized Medical Imaging and Graphics, vol. 38, no. 8,
pp. 753–763, 2014.
[42]
S. Hegenbart, A. Uhl, A. V´ecsei, and G. Wimmer, “Scale invariant texture
descriptors for classifying celiac disease,” Medical image analysis, vol. 17,
no. 4, pp. 458–474, 2013.
[43]
K. He, X. Chen, S. Xie, Y. Li, P. Doll´ar, and R. Girshick, “Masked autoencoders are scalable vision learners,” in Proceedings of the IEEE/CVF
conference on computer vision and pattern recognition, 2022, pp. 16 000–
16 009.
[44]
I. Loshchilov, “Decoupled weight decay regularization,” arXiv preprint
arXiv:1711.05101, 2017.
[45]
X. Luo, W. Liao, J. Xiao, et al., “Word: A large scale dataset, benchmark
and clinical applicable study for abdominal organ segmentation from ct
image,” Medical Image Analysis, vol. 82, p. 102 642, 2022.
[46]
A. Taore, M. Tiang, and S. C. Dakin, “(the limits of) eye-tracking with
ipads,” Journal of Vision, vol. 24, no. 7, pp. 1–1, 2024.
[47]
P. Blignaut and T. Beelders, “The effect of fixational eye movements on fixation identification with a dispersion-based fixation detection algorithm,”
Journal of eye movement research, vol. 2, no. 5, 2008.
[48]
B. Rister, D. Yi, K. Shivakumar, T. Nobashi, and D. L. Rubin, “Ct-org,
a new dataset for multiple organ segmentation in computed tomography,”
Scientific Data, vol. 7, no. 1, p. 381, 2020.


<!-- Page 73 -->

BIBLIOGRAPHY
[49]
Y. Ji, H. Bai, C. Ge, et al., “Amos: A large-scale abdominal multi-organ
benchmark for versatile medical image segmentation,” Advances in neural
information processing systems, vol. 35, pp. 36 722–36 732, 2022.
[50]
I. J. Goodfellow, Y. Bengio, and A. Courville, Deep Learning. Cambridge,
MA, USA: MIT Press, 2016, http://www.deeplearningbook.org.
[51]
Y. Bengio, A. Courville, and P. Vincent, “Representation learning: A review
and new perspectives,” IEEE transactions on pattern analysis and machine
intelligence, vol. 35, no. 8, pp. 1798–1828, 2013.
[52]
Y. LeCun, Y. Bengio, and G. Hinton, “Deep learning,” nature, vol. 521,
no. 7553, pp. 436–444, 2015.
[53]
C. M. Bishop, Neural Networks for Pattern Recognition. USA: Oxford
University Press, Inc., 1995, ISBN: 0198538642.
[54]
J. Kiefer and J. Wolfowitz, “Stochastic estimation of the maximum of a
regression function,” The Annals of Mathematical Statistics, vol. 23, no. 3,
pp. 462–466, 1952. [Online]. Available: https://doi.org/10.1214/aoms/
1177729392.
[55]
D. Kingma and J. Ba, “Adam: A method for stochastic optimization,”
International Conference on Learning Representations, Dec. 2014.
[56]
J. Duchi, E. Hazan, and Y. Singer, “Adaptive subgradient methods for
online learning and stochastic optimization.,” Journal of machine learning
research, vol. 12, no. 7, 2011.
[57]
“Lecture 6.5-rmsprop: Divide the gradient by a running average of its recent
magnitude,” COURSERA: Neural networks for machine learning, vol. 4,
no. 2, p. 26, 2012.


<!-- Page 74 -->

BIBLIOGRAPHY
[58]
S. Ioffe and C. Szegedy, “Batch normalization: Accelerating deep network
training by reducing internal covariate shift,” in International conference
on machine learning, pmlr, 2015, pp. 448–456.
[59]
J. L. Ba, J. R. Kiros, and G. E. Hinton, “Layer normalization,” arXiv
preprint arXiv:1607.06450, 2016.
[60]
N. Srivastava, G. Hinton, A. Krizhevsky, I. Sutskever, and R. Salakhutdinov, “Dropout: A simple way to prevent neural networks from overfitting,”
The journal of machine learning research, vol. 15, no. 1, pp. 1929–1958,
2014.
[61]
R. Yamashita, M. Nishio, R. K. G. Do, and K. Togashi, “Convolutional
neural networks: An overview and application in radiology,” Insights into
imaging, vol. 9, pp. 611–629, 2018.
[62]
A. Ghosh, A. Sufian, F. Sultana, A. Chakrabarti, and D. De, “Fundamental
concepts of convolutional neural network,” Recent trends and advances in
artificial intelligence and Internet of Things, pp. 519–567, 2020.
[63]
A. Vaswani, “Attention is all you need,” Advances in Neural Information
Processing Systems, 2017.
[64]
A. Dosovitskiy, L. Beyer, A. Kolesnikov, et al., “An image is worth 16x16
words: Transformers for image recognition at scale,” in 9th International
Conference on Learning Representations, ICLR, 2021.
[65]
J. Devlin, M.-W. Chang, K. Lee, and K. Toutanova, “Bert: Pre-training
of deep bidirectional transformers for language understanding,” in Proceedings of the 2019 Conference of the North American Chapter of the


<!-- Page 75 -->

BIBLIOGRAPHY
Association for Computational Linguistics: Human Language Technologies, Volume 1, 2019. DOI: 10.18653/v1/N19-1423.
[66]
K. He, X. Zhang, S. Ren, and J. Sun, “Deep residual learning for image
recognition,” in Proceedings of the IEEE conference on computer vision
and pattern recognition, 2016, pp. 770–778.


<!-- Page 76 -->

Appendix A
Prerequisite Concepts
A.1
Deep Learning Essentials
Deep Learning.
AI is a rapidly developing area of Computer Science with
diverse applications and research topics, including, e.g., task automation, speech
and image recognition, and medical diagnosis. Within AI, Machine Learning
focuses on enabling computers to extract patterns from raw data [50]. Machine
learning encompasses feature engineering to solve a classification or regression
task. However, when dealing with unstructured data, manual feature engineering
is particularly challenging. Furthermore, handcrafted features designed for one
specific task may not be applicable or effective for another task. In contrast,
Representation Learning allows machines to learn necessary transformations of
the data, namely representations, that make it easier to extract useful information
from data [51].
Deep Learning, a subfield of Representation Learning, uses
multiple levels of abstraction, transforming raw input through simple, non-linear
modules into progressively more abstract representations [52].
In contrast to
traditional Machine Learning models, Deep Learning models can automatically


<!-- Page 77 -->

### A.1 Deep Learning Essentials
learn representations from raw data, making them quite powerful for unstructured
data, including images, text, or audio.
Introduction to Neural Networks.
Artificial Neural Networks (ANNs) are
Deep Learning models inspired by neural connections in the biological brain.
They are designed to recognize patterns and solve complex problems. An artificial
neuron is a mathematical function f : RM →R mapping a vector containing M
input values, or features, x ∈RM into output value ˆy ∈R. Specifically, the
function f = wTx + b computes a linear combination of inputs with learnable
parameters w ∈RM, also known as weights, and adds a bias term b ∈R. It can
be noted that such a single neuron can be viewed as a linear regression model that
can be optimized using gradient-based techniques to approximate ground truth
values of target variable y.
Multilayer Perceptron.
A single neuron was extended to a Multilayer Perceptron (MLP), also known as a feedforward neural network. An MLP might include
multiple intermediate, or hidden, layers, and contain multiple outputs. Each neuron in one layer is connected to every neuron in the subsequent layer, forming a
fully connected architecture [50]. Thus, stacking of artificial neurons into multiple
layers forms neural networks in their simplest form.
Activation functions.
A crucial component of neural networks is an activation function that is applied to the output of each neuron. Activation functions
introduce non-linearity, allowing neural networks to learn complex, non-linear
relationships in the data [53]. The frequently exploited activation functions and
their mathematical notations are listed as follows:


<!-- Page 78 -->

### A.1 Deep Learning Essentials
• Sigmoid: σ(x) =
1+e−x, where the output is in [0, 1]. Used in the output
layer for a binary classification task [50].
• Softmax: σ(xi) =
exi
PK
j=1 exj , where the output is a probability distribution
over the K classes, with each output value in [0, 1]. Used in the output layer
for a multi-class classification task [50].
• Hyperbolic tangent: tanh(x) = ex−e−x
ex+e−x, where the output is in [−1, 1]. Used
in hidden layers [52].
• Rectified Linear Unit (ReLU): f(x) = max(0, x), where the output is in
[0, ∞). Widely used in hidden layers [52].
• Leaky ReLU: f(x) =





x
if x ≥0
αx
if x < 0
, where α is a small positive constant.
Used in hidden layers [52].
Loss functions.
Training the neural network is the process of optimizing the
model parameters, or weights, to minimize the error between the model’s outputs
and ground truth labels from the dataset. In a nutshell, given a dataset D =
{(xi, yi)}N
i=1, the goal of the neural network is to approximate an unknown function
f in order to minimize the error, or loss function L(y,ˆy), where y and ˆy are ground
truth labels and the model’s predictions, respectively. Loss functions commonly
used in Deep Learning are outlined as follows:
• Mean Squared Error (MSE):
L(y,ˆy) = 1
N
N
X
i=1
(yi −ˆyi)2,
(A.1)


<!-- Page 79 -->

### A.1 Deep Learning Essentials
where yi is the ground truth label, ˆyi is the output of the neural network, and
N is the batch size. Commonly used for the regression task [50].
• Binary Cross-Entropy (CE):
L(y,ˆy) = −1
N
N
X
i=1
(yi log(ˆyi) + (1 −yi) log(1 −ˆyi)),
(A.2)
where yi is the ground truth label, ˆyi is the output of the neural network, and
N is the batch size. Used for the binary classification [50].
• Categorical Cross-Entropy (CE):
L(y,ˆy) = −1
N
N
X
i=1
K
X
j=1
(yi,j log(ˆyi,j)),
(A.3)
where yi is the true label, ˆyi is the output, N is the batch size, and K is the
number of classes in the multiclass classification [50].
Gradient-based optimization.
Considering a network with a differentiable loss
function, the error optimization can be achieved using algorithms based on gradient descent, e.g., Stochastic Gradient Descent (SGD) [54] and Adam [55]. The
former is the basic optimization algorithm for training neural networks. SGD is
an iterative optimization algorithm that updates the model parameters by taking
small steps in the direction of the negative gradient of the loss function. The
gradient is computed using a small subset drawn uniformly from the training data,
called a minibatch [50]. This makes SGD computationally efficient and able to
handle large datasets. The gradient of the loss is propagated backwards through
the network using the chain rule of calculus to update the parameters of the net-


<!-- Page 80 -->

### A.1 Deep Learning Essentials
work on the earlier layers. This process is called back-propagation. For notational
simplicity, it is convenient to group all model parameters, including weights and
biases, together in a single weight matrix w [53]. Formally, the update rule for
network parameters wt can be formulated as:
wt = wt−1 −ϵ∇wL,
(A.4)
where ϵ is the learning rate, a positive scalar that determines the magnitude
of updates [50].
An extended version of SGD, Adam proposed by Kingma and Ba [55], has
seen broader adoption for applications in the fields of Computer Vision and Natural
Language Processing. The Adam optimization method utilizes both momentum
and scaling, combining the advantages of two other extensions of SGD, such as
AdaGrad [56] and RMSProp [57]. The Adam algorithm maintains two moving
averages for each parameter: the first moment as a mean of gradients and the
second moment as an uncentered variance of gradients. This makes it particularly
effective in handling challenges arising from noisy data or sparse gradients. The
update rule for model parameters is defined as follows:
mt = β1mt−1 + (1 −β1)∇wL,
(A.5)
vt = β2vt−1 + (1 −β2)(∇wL)2,
(A.6)
ˆmt =
mt
1 −βt
,
ˆvt =
vt
1 −βt
(A.7)


<!-- Page 81 -->

### A.1 Deep Learning Essentials
wt = wt−1 −ϵ
ˆmt
√ˆvt + ϵ,
(A.8)
where mt and vt are the first and second moment estimates, respectively, β1
and β2 are the decay rates, ϵ is a small constant denoted to prevent division by
zero, and ϵ is the learning rate [55].
Training, validation, testing.
The development of machine learning models
typically involves three key phases: training, validation, and testing. The training process involves feeding the model with input data and changing its internal
parameters to minimize a predefined loss function. To evaluate the model generalization ability (i.e., the ability of the model to perform well on new previously
unseen data) during training, a separate validation set is used [50]. The validation
set provides feedback on the model’s performance on unseen data, helping to tune
hyperparameters, prevent overfitting, and determine early stopping criteria.
A common challenge during training is overfitting, where the model performs well on the training data but poorly on the validation or test set, indicating it
has learned patterns specific to the training set rather than general features. Conversely, underfitting occurs when the model performs poorly on both the training
and validation sets, suggesting it has not fit the data. A well-trained Machine
Learning model should achieve a balance between underfitting and overfitting.
Once the model has been trained, its performance is evaluated on unseen
data or a test set. The testing stage, which is required to make a final measurement
of model performance, for example, to state the final value of the model. In Deep
Learning, the model’s inference phase refers to using the trained model to make
predictions on new, previously unseen data.


<!-- Page 82 -->

### A.2 Computer Vision Architectures
Regularization techniques.
To mitigate overfitting and improve generalization
ability, various model modifications, called as regularization techniques, can be
applied during training.
One of the most common regularization strategies in Deep Learning is a
weight decay, also known as L2 regularization, which penalizes large weights by
adding a term proportional to the squared magnitude of the weights to the loss
function [50]. This encourages the model to maintain smaller weights.
Another method, called Batch Normalization or BatchNorm, applies a normalization operation to every mini-batch after the activation function of a certain
layer in the neural network [58]. Layer Normalization or LayerNorm, in contrast,
normalizes across the features of individual data points and is particularly effective in Transformer models [59]. Another widely adopted method is Dropout,
which is based on the random elimination of a fraction of input during training.
This technique helps prevent the network from becoming overly reliant on specific
neurons and forces it to learn more robust representations [60]. Various regularization techniques are often used in combination to achieve a balance between
model complexity and generalization performance.
A.2
Computer Vision Architectures
Convolutional Neural Networks.
ConvolutionalNeuralNetworks(CNNs)have
demonstrated considerable success in various Computer Vision tasks. This type
of networks is specifically designed to process data with a grid-like structure,
such as image data that can be represented as a two-dimensional grid of pixels
[50]. CNNs comprise three primary types of layers: convolutional layers, pooling
layers, and fully connected layers. The former are responsible for automatically


<!-- Page 83 -->

### A.2 Computer Vision Architectures
learning spatial hierarchies of features, enabling the network to capture patterns
that range from low-level edges to high-level shapes.
Together with pooling
layers, which reduce the dimensionality of feature maps, these layers focus on
feature extraction. Subsequently, fully connected layers use the extracted features
to produce a final output, such as a classification result [61].
The convolution operation is a specialized kind of linear operation that is
essential for feature extraction in the CNN architecture. According to Goodfellow
et al. [50], given a two-dimensional image I and a two-dimensional kernel K, the
convolution operation, denoted by an asterisk (∗), can be formally defined as:
S(i, j) = (I ∗K)(i, j) =
X
m
X
n
I(i + m, j + n)K(m, n),
(A.9)
where i and j are the pixel indices of the output, or a feature map S.
The equation above describes how convolution works on a small part of the
image. In order to apply the convolution operation across the entire image, the
kernel is moved as a sliding window, performing element-wise multiplications
with parts of an image it covers. A visualization of how convolution operates on
a two-dimensional pixel matrix, or tensor, is illustrated in Fig. A.1.
As it can be observed, both height and width of the output feature map are
reduced compared to the input shape. This can be explained by the fact that the
center of the kernel cannot overlap with the outermost element of the input matrix
[61]. However, the size of the feature map can be controlled by hyperparameters
such as kernel size, padding, and stride. Kernel size determines the width and
height of the kernel matrix. Padding refers to the addition of extra zero pixels
around edges of the input matrix, while stride defines the step size of the sliding
window as it moves across the input matrix.


<!-- Page 84 -->

### A.2 Computer Vision Architectures
Fig. A.1. An example of convolution applied to a 2D input tensor (Fig. 3c, [61]).
The output size of convolution operation might be calculated as follows:
h′ = h −f + p
s
+ 1,
(A.10)
w′ = w −f + p
s
+ 1,
(A.11)
where h′ and w′ represent the height and width of the output matrix, respectively; h and w indicate the height and width of the input matrix, respectively; f
denotes the kernel size, p is the padding, and s is the stride [62].
Digital images quite often have three color channels (RGB), which can be
represented as a three-dimensional matrix. Consequently, the kernels also need
to be three-dimensional, allowing the convolution operation to be applied independently to each channel. The results for each channel are then summed up,
producing a two-dimensional matrix from a single kernel. However, in CNN,
one convolutional layer typically contains multiple kernels. As a result, each
kernel acts as a sliding window during the convolution process, and the output
of the layer is a three-dimensional tensor, with the size of the third dimension


<!-- Page 85 -->

### A.2 Computer Vision Architectures
corresponding to the number of kernels used or the depth of the layer.
In the context of CNNs, kernels are sets of learnable parameters similar to
the weight parameters of usual neural networks. Additionally, after performing
the convolution, the bias is added to the result, and a nonlinear activation function,
such as ReLU, is applied. After this stage, a pooling operation is typically applied
to the output of the convolutional layer. To optimize the parameters of the kernels
during training, back-propagation is used.
Pooling is a downsampling technique that reduces spatial dimensions, specifically, height and width of the feature maps. This operation subsequently decreases
computational costs by reducing the number of parameters. Pooling works by applying a sliding window and mapping the values within each window to a single
output value. Similarly, a pooling operation has a sliding filter size and stride.
Among various pooling methods, max pooling is the most widely exploited. It
simply selects the maximum value in each window. Unlike the spatial dimensions,
the depth of the feature maps remains unchanged.
Fig. A.2. An example of max pooling applied to a 2D tensor (Fig. 6a, [61]).
As demonstrated in Fig. A.2, applying a max pooling with a filter size of 2×2,
no padding, and a stride of 2, splits the input feature map into non-overlapping


<!-- Page 86 -->

### A.2 Computer Vision Architectures
2 × 2 patches filled with maximal values. Unlike convolutional layers, pooling
layers do not contain any learnable parameters. Nevertheless, they influence the
network training process. For instance, max pooling prevents the non-maximal
values of the feature maps from changing during back-propagation.
Vision Transformers.
Transformers, originally introduced by Vaswani et al.
[63], have shown impressive performance in the field of Natural Language Processing (NLP). Building on this success, Dosovitskiy et al. [64] proposed Vision
Transformers (ViTs) as a compelling alternative to CNNs for Computer Vision
tasks. Unlike CNNs, which rely on local receptive fields and hierarchical feature
extraction, ViTs employ a self-attention mechanism to capture global dependencies within images. The self-attention is based on relating different positions of
a single sequence, or in our case patches of image in order to compute a representation of image [63]. This allows ViTs to process images as sequences of
patches, enabling them to learn contextual relationships. The ViT model overview
is provided in Fig. A.3.
Fig. A.3. ViT model architecture (Figure 1, [64]).


<!-- Page 87 -->

### A.2 Computer Vision Architectures
Formally, a two-dimensional input image x ∈RH×W×C, where H, W, and C
are the height, width, and number of channels, respectively, is divided into patches
of size P × P. Subsequently, each patch is flattened into a vector xi
p ∈RP2·C. This
process transforms the image into a sequence of N patches, where N = H·W
P2 .
Therefore, the input image can be represented as follows:
z0 = [x1
pE; x2
pE; . . . ; xN
p E],
(A.12)
where xi
p ∈RP2·C is the flattened i-th patch, E ∈R(P2·C)×D is a trainable
linear projection layer used to map flattened patches into D-dimensional patch
embeddings.
Originally, the training objective of ViTs is based on image classification,
therefore, a special learnable embedding [class] [65] is prepended to the sequence
of embedded patches. This special embedding serves as the image representation
y (from Eq. A.16) in order to obtain the classification output for the image.
Additionally, to retain positional information, learnable positional embeddings
are added to the patch embeddings, resulting in the following sequence:
z0 = [xclass; x1
pE; x2
pE; . . . ; xN
p E] + Epos,
(A.13)
where xclass ∈RD is a special learnable class embedding and Epos ∈R(N+1)×D
define positional embeddings [64].
From here, the sequence z0 is then fed into the Transformer encoder that
follows an encoder structure, which aims to map an input sequence of representations (x1, . . . , xn) to a sequence of latent representations z = (z1, . . . , zn) [63]. The
architecture of Transformer encoder comprises alternating layers of multi-head
self-attention (MSA) and MLP blocks (Eq. A.14, Eq. A.15), followed by Layer


<!-- Page 88 -->

### A.2 Computer Vision Architectures
Normalization (LN) and residual connections [66] before and after each block,
respectively. More formally, these operations can be expressed as:
z′
l = MSA(LN(zl−1)) + zl−1,
(A.14)
zl = MLP(LN(z′
l)) + z′
l,
(A.15)
y = LN(z0
L),
(A.16)
where l = 1 . . . L denotes the index of the layer [64].
Self-Attention (SA) [63], is a mechanism designed to capture dependencies
within a sequence by computing the relevance of each token with respect to all
others.
In the context of SA, each input token is first transformed into three
vectors: queries (Q), keys (K), and values (V), which are learned representations
used to compute attention weights. Queries determine what each token is looking
for, keys describe what each token offers, and values carry the actual information
of the token. In a nutshell, given the input sequence z ∈RN×D, SA reweighs each
element zi using weights computed based on pairwise similarities with all elements
in z. Therefore, it returns a sequence of the same dimensionality (from Eq. A.18).
SA block involves three matrices obtained using learnable linear transformations,
i.e., queries, keys, and values: [Q, K, V] = zW [q,k,v], where W [q,k,v] ∈RN×Dk. The
attention weights A ∈RN×N and self-attention can be calculated as follows:
A = softmax(QKT
√Dk
),
(A.17)


<!-- Page 89 -->

### A.2 Computer Vision Architectures
SA(z) = AV.
(A.18)
Similarly, multi-head self-attention (MSA) projects the queries, keys, and
values h times, also called heads, instead of performing a single self-attention.
Following this, self-attention with h heads can be defined as follows:
MSA(z) = [SA1(z); SA2(z); . . . ; SAh(z)]W o,
(A.19)
where W o ∈Rh·Dk×D [64]. Thus, MSA performs multiple self-attention processes in parallel, where each head learns to capture its own type of relationships
within the input sequence.


<!-- Page 90 -->

Appendix B
Defining optimal prompts
B.1
Evaluation on Synthetic Data
In this study, we trained and evaluated models with different types of input
prompts to determine the most effective model setup for our gaze-assisted system.
Specifically, we evaluated the MedSAM model fine-tuned on prompts with various
numbers of points: 20 points, 50 points, and a random number of input points
ranging from 1 to 20. The points were generated with 80% inside the ground
truth segmentation mask and 20% – outside this mask. Furthermore, we explored
fine-tuning the model using both point prompts and base prediction masks. These
base masks were generated using MedSAM with bounding boxes drawn around
ground truth masks. For this approach, points were sampled with 70% randomly
generated from the difference area between the reference and prediction masks,
20% – from the reference mask, and 10% – from outside the mask. We also tested
a strategy in which a random number of points was selected for each case, with
unused points padded using a special "not a point" (-1) label and active points
labeled as "foreground" (1).


<!-- Page 91 -->

### B.1 Evaluation on Synthetic Data
All models were fine-tuned and evaluated using a randomly selected 5%
subset of the WORD dataset. For both training and testing, prompts to the model
were generated using the same approach.
As shown in Table B.1, the model strategies using 50-point and 20-point
prompts achieved the highest performance with a mean DSC of 91.82% and
90.59% across all 16 classes, respectively.
TABLE B.1
Comparison of segmentation performance (DSC (%)) for models fine-tuned using
different prompting strategies. For random-length prompts, the number of points
was sampled from uniform distribution within the ranges * – [1; 20], ** – [2;
20], and *** – [2; 50]. The best results are shown in bold; the second-best are
underlined.
Prompt
Random #
pts*
20 pts
50 pts
Base mask +
20 pts
Base mask +
random # pts**
Base mask +
random # pts***
Liver
92.45
95.34
95.69
92.52
92.03
93.66
Spleen
94.69
95.73
95.74
92.32
92.85
93.23
Kidney (L)
92.22
95.67
96.01
94.42
94.21
94.84
Kidney (R)
91.23
95.89
96.06
94.21
94.02
94.49
Stomach
91.64
95.25
95.55
93.12
92.53
93.91
Gallbladder
83.03
90.74
91.45
86.53
86.93
88.11
Esophagus
83.85
86.32
88.42
80.75
81.67
81.76
Pancreas
80.32
88.46
89.96
82.99
86.04
86.57
Duodenum
79.48
86.85
89.45
80.05
82.60
83.11
Colon
82.07
89.85
91.25
83.64
84.58
85.69
Intestine
80.59
88.51
90.29
81.94
83.61
84.52
Adrenal
75.87
78.44
80.18
74.09
76.56
75.40
Rectum
84.97
90.23
91.14
84.31
86.70
87.18
Bladder
92.09
95.63
96.16
91.95
92.03
93.81
H. femur (L)
88.20
92.18
93.10
84.95
86.77
87.31
H. femur (R)
86.91
93.71
94.11
86.92
89.41
89.09
Mean
84.80
90.59
91.82
85.39
86.47
87.31
Based on the results above, we selected both models with 20-point and 50point prompts for further evaluation with the proxy radiologist and compared their
segmentation quality in a real-time scenario.


<!-- Page 92 -->

### B.2 Evaluation with Clinicians
B.2
Evaluation with Clinicians
To compare models and select the best one, we instructed one of the proxy
radiologists to segment 54 organs in various slices (subset used in Section 5.1)
using each model. According to Table B.2, the best performance was achieved
with the 20-point model using randomly selected gaze points, which outperformed
the other strategies in both accuracy and consistency across various abdominal
organs. Even though the 50-point model performed well in some cases, its overall
performance was slightly lower. Therefore, the model with 20-point prompts was
ultimately considered the best-performing gaze-assisted model and used for the
main experiments with clinicians.
TABLE B.2
Segmentation performance (DSC (%)) using different prompts with 20 and 50
points across three strategies for selecting gaze points for model inference, such
as random points (Random), fixations with return (Fixs w/ return), and fixations
with addition (Fixs w/ add). The best results are highlighted in bold.
Prompt
20 points
50 points
Strategy
Random
Fixs w/ return
Fixs w/ add
Random
Fixs w/ return
Fixs w/ add
Liver
97.26
39.71
95.62
96.33
24.95
95.87
Spleen
95.49
72.62
94.14
95.40
87.91
94.60
Kidney (L)
95.94
95.85
95.01
95.03
49.02
86.68
Kidney (R)
93.68
75.09
88.80
78.05
24.84
86.43
Stomach
88.84
51.57
90.12
95.56
67.44
92.56
Gallbladder
92.01
85.14
90.77
87.84
85.51
89.41
Esophagus
92.89
14.25
62.07
72.60
82.07
87.53
Pancreas
94.38
49.61
91.58
91.82
83.88
91.66
Duodenum
84.82
79.33
86.11
81.68
78.79
78.60
Colon
88.44
67.35
90.76
86.64
77.09
91.28
Intestine
83.23
71.04
85.54
81.03
70.51
85.12
Adrenal
79.57
72.58
76.93
61.66
54.41
78.83
Rectum
90.62
79.12
92.69
92.23
75.82
92.67
Bladder
96.60
95.01
82.50
96.37
87.25
93.90
H. Femur (L)
93.34
78.31
92.28
89.61
92.27
92.54
H. Femur (R)
87.71
57.33
87.10
87.23
83.32
83.47
Mean
88.90
67.68
87.61
86.16
71.22
87.94

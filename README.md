## Model Development & Optimization

### Model Architecture

The project uses **MobileNetV3-Small** as the primary image classification
architecture because it is designed for lightweight deployment and
edge-device applications.

### Dataset

The model was trained and evaluated using the prepared PlantVillage dataset.

| Split | Images |
|---|---:|
| Training | 16,499 |
| Validation | 2,062 |
| Testing | 2,063 |
| Total | 20,624 |

The classification task contains **15 crop disease/healthy-leaf classes**.

### Training and Fine-Tuning

An initial frozen MobileNetV3-Small model achieved:

- Accuracy: **90.89%**
- Precision: **91.35%**
- Recall: **90.89%**
- F1-score: **90.93%**

The model was subsequently fine-tuned by unfreezing the final portion of
the MobileNetV3-Small backbone.

The fine-tuned model achieved:

- Accuracy: **93.21%**
- Precision: **93.43%**
- Recall: **93.21%**
- F1-score: **93.23%**

### TensorFlow Lite Conversion

The fine-tuned FP32 model was converted to TensorFlow Lite.

The TFLite FP32 model preserved the same test performance:

- Accuracy: **93.21%**
- Precision: **93.43%**
- Recall: **93.21%**
- F1-score: **93.23%**

The resulting model size was **3.60 MB**.

Measured mean CPU inference latency in the Kaggle evaluation environment
was **5.720 ms**.

### INT8 Quantization Experiment

Post-training INT8 quantization was investigated to reduce model size for
potential edge deployment.

| Metric | FP32 TFLite | INT8 TFLite |
|---|---:|---:|
| Accuracy | 93.21% | 59.04% |
| Precision | 93.43% | 79.75% |
| Recall | 93.21% | 59.04% |
| F1-score | 93.23% | 61.48% |
| Model size | 3.60 MB | 1.18 MB |
| Mean CPU latency | 5.720 ms | 13.531 ms |

INT8 quantization reduced the model size by approximately **67.2%**.
However, it caused a substantial reduction in classification performance.

A second calibration experiment using 500 representative training images
was also investigated, but the accuracy degradation remained.

### Optimization Challenges

During INT8 model verification, an XNNPACK delegate error was encountered.
The model was subsequently tested without the default delegate and was able
to perform INT8 inference.

The INT8 model nevertheless showed substantial performance degradation.

Quantization-Aware Training (QAT) was investigated as a possible solution.
TensorFlow Model Optimization Toolkit (TFMOT) version 0.8.1 was installed,
but applying the QAT API in the TensorFlow 2.20.0 environment resulted in a
Keras/TFMOT compatibility error.

Therefore, the verified **FP32 TFLite model** was retained as the current
high-accuracy deployment candidate, while the INT8 result and optimization
issues were documented for further investigation.

### Model Development Artifacts

- `notebooks/05_model_development.ipynb`
- `results/model_results.csv`
### Treatment Mapper

The Treatment Mapper connects the predicted disease class from the MobileNetV3-Small classifier to corresponding treatment, prevention and project-level severity information.

The mapper supports all 15 disease/healthy-leaf classes used by the classifier.

#### Treatment Mapper Components

- `src/treatment/treatment_mapper.py` — loads disease information and returns treatment recommendations.
- `src/treatment/treatment_mapping.json` — stores treatment, prevention and severity information for all 15 classes.
- `tests/test_treatment_mapper.py` — validates known disease mappings and unknown-disease handling.

#### Inference Integration

The TFLite inference pipeline was integrated with the Treatment Mapper.

The inference flow is:

```text
Leaf Image
    ↓
MobileNetV3-Small FP32 TFLite Model
    ↓
Predicted Disease + Confidence
    ↓
Treatment Mapper
    ↓
Severity + Treatment + Prevention
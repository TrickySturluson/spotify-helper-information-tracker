# Optional local audio mood models

SHIT already extracts local acoustic measurements through `scripts/music/audio_analysis.py`. This optional extension adds continuous **valence** and **arousal** estimates from a pretrained Essentia model. It is deliberately separate from the Spotify metadata workflow: it requires audio files that the user has legally obtained and does not download, stream, or extract Spotify audio.

## Why DEAM is the first candidate

Essentia publishes the `deam-msd-musicnn-2` regression model. Its metadata describes two outputs in the valence/arousal domain on a 1–9 scale, trained using the DEAM dataset of 1,802 songs. The published metadata reports:

| Dimension | Concordance correlation | Pearson correlation | RMSE |
|---|---:|---:|---:|
| Valence | 0.778 | 0.738 | 0.635 |
| Arousal | 0.647 | 0.773 | 0.674 |

These are reported dataset metrics, not a guarantee of performance on the user's library. The model's outputs are regression estimates, not calibrated probabilities or confidence tiers. The script stores mean and standard deviation across model frames, plus model version, metadata and weight hashes, dataset metrics, source filename and source audio hash. The sequencer does **not** consume these scores yet.

## Model files

Download these files directly from the official Essentia model repository and place them under `models/essentia/deam/`:

- Embedding model: [msd-musicnn-1.pb](https://essentia.upf.edu/models/feature-extractors/musicnn/msd-musicnn-1.pb)
- DEAM regression model: [deam-msd-musicnn-2.pb](https://essentia.upf.edu/models/classification-heads/deam/deam-msd-musicnn-2.pb)
- Metadata: [deam-msd-musicnn-2.json](https://essentia.upf.edu/models/classification-heads/deam/deam-msd-musicnn-2.json)

The script validates model name, version and output class order before inference. It does not download model weights automatically and does not store them in Git.

## Installation and use

Essentia's TensorFlow-enabled package is separate from the standard audio-analysis package:

```bash
pip install essentia-tensorflow numpy
python compat/analyze_audio_mood.py "/path/to/legally-obtained-audio" --accept-noncommercial-license
```

Files must be named `Artist - Track.ext`, matching the existing local audio analysis convention. Supported extensions are MP3, FLAC, WAV, OGG, M4A and AIFF. The default output is `assistant_data/music/audio_mood_profiles.json`. Unchanged audio/model pairs are skipped by SHA-256 and model version. The tool stores derived descriptors only, never audio bytes or full local paths.

The official Essentia TensorFlow installation documentation describes package support for Linux/macOS; Windows users may need WSL2 or a source build. This has not been validated on native Windows.

## License caution

Essentia's current general licensing page says pretrained models are under **CC BY-NC-ND 4.0**, while the model catalogue page has described MTG models as **CC BY-NC-SA 4.0**. These official pages conflict. Both indicate non-commercial restrictions. Confirm the applicable terms with Music Technology Group before use beyond personal non-commercial experimentation, and do not redistribute the model weights. The command requires an explicit `--accept-noncommercial-license` acknowledgement but that flag is not a legal determination.

## Why predictions are not yet used for sorting

Before using model output to influence sequencing, we need a representative, human-reviewed sample from the actual library and a calibration/validation report. Until then:

- raw valence/arousal values remain separate from acoustic confidence and community mood tags;
- model output cannot promote track mood confidence;
- no probability thresholds or mood labels are inferred from arbitrary score cutoffs;
- the model remains opt-in and local-only.

## References

- [Essentia DEAM model metadata](https://essentia.upf.edu/models/classification-heads/deam/deam-msd-musicnn-2.json)
- [DEAM dataset](https://cvml.unige.ch/databases/DEAM/)
- [Essentia TensorFlow installation and inference](https://essentia.upf.edu/machine_learning.html)
- [Essentia model catalogue](https://essentia.upf.edu/models.html)
- [Essentia licensing information](https://essentia.upf.edu/licensing_information.html)

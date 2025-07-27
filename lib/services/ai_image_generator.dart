import 'dart:convert';
import 'dart:typed_data';
import 'package:firebase_vertexai/firebase_vertexai.dart';

class AIImageGenerator {
  final model = FirebaseVertexAI.instance.imagenModel(
    model: 'imagen-3.0-generate-002',
    generationConfig: ImagenGenerationConfig(numberOfImages: 4),
  );

  Future<List<Uint8List>> generateImages(String text) async {
    final res = await model.generateImages(text,);

    if (res == null || res.images == null) {
      return [];
    }

    final images =
        res.images!.map((e) => e.bytesBase64Encoded).toList();

    return images;
  }
}

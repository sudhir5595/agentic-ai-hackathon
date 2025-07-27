import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../services/ai_image_generator.dart';

class ImageGeneratorScreen extends StatefulWidget {
  const ImageGeneratorScreen({super.key});

  @override
  _ImageGeneratorScreenState createState() => _ImageGeneratorScreenState();
}

class _ImageGeneratorScreenState extends State<ImageGeneratorScreen> {
  final TextEditingController _controller = TextEditingController();
  final AIImageGenerator _aiImageGenerator = AIImageGenerator();
  bool _isLoading = false;
  List<Uint8List> _images = [];

  Future<void> _generateImages() async {
    if (_controller.text.trim().isEmpty) {
      return;
    }

    setState(() {
      _isLoading = true;
      _images = [];
    });

    try {
      final images = await _aiImageGenerator.generateImages(_controller.text);
      setState(() {
        _images = images;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error generating images: $e')),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Image Generator'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            TextField(
              controller: _controller,
              decoration: const InputDecoration(
                labelText: 'Enter a prompt',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _isLoading ? null : _generateImages,
              child: _isLoading
                  ? const CircularProgressIndicator()
                  : const Text('Generate Images'),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : _images.isEmpty
                      ? const Center(child: Text('No images generated yet.'))
                      : GridView.builder(
                          gridDelegate:
                              const SliverGridDelegateWithFixedCrossAxisCount(
                            crossAxisCount: 2,
                            crossAxisSpacing: 8,
                            mainAxisSpacing: 8,
                          ),
                          itemCount: _images.length,
                          itemBuilder: (context, index) {
                            return Image.memory(_images[index]);
                          },
                        ),
            ),
          ],
        ),
      ),
    );
  }
}

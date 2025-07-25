import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:image_picker/image_picker.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:video_thumbnail/video_thumbnail.dart';
import 'package:photo_gallery/photo_gallery.dart';

void main() {
  runApp(const SahayakApp());
}

class SahayakApp extends StatelessWidget {
  const SahayakApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Sahayak - AI Teaching Assistant',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        brightness: Brightness.light,
        scaffoldBackgroundColor: Colors.white,
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.deepPurple,
          foregroundColor: Colors.white,
        ),
        textTheme: const TextTheme(
          bodyMedium: TextStyle(color: Colors.black87),
        ),
      ),
      home: const TeacherDashboard(),
    );
  }
}

class TeacherDashboard extends StatefulWidget {
  const TeacherDashboard({super.key});

  @override
  _TeacherDashboardState createState() => _TeacherDashboardState();
}

class _TeacherDashboardState extends State<TeacherDashboard> {
  int _selectedIndex = 0;

  final List<Widget> _pages = [
    const ChatScreen(),
    const ContentCreationScreen(),
    const LessonPlannerScreen(),
    const TextbookAnalyzerScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _pages[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        selectedItemColor: Colors.deepPurple,
        unselectedItemColor: Colors.grey,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.chat),
            label: 'Ask Sahayak',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.create),
            label: 'Create Content',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.calendar_today),
            label: 'Lesson Plans',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.book),
            label: 'Textbook Helper',
          ),
        ],
      ),
    );
  }
}

// ==================== ChatScreen ====================

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  _ChatScreenState createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final List<Map<String, dynamic>> _messages = [];
  late stt.SpeechToText _speech;
  final ImagePicker _picker = ImagePicker();
  bool _isListening = false;
  String _speechText = '';

  @override
  void initState() {
    super.initState();
    _speech = stt.SpeechToText();
    _addWelcomeMessage();
  }

  void _addWelcomeMessage() {
    setState(() {
      _messages.add({
        "role": "assistant",
        "content":
            "Hello! I'm Sahayak, your AI Teaching Assistant. I am here to help you create localized educational content, develop lesson plans, and assist you with your multi-grade classroom teaching. You can type your questions or upload an image of a textbook page to get started."
      });
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    _speech.stop();
    super.dispose();
  }

  void _sendMessage(String message) async {
    setState(() {
      _messages.add({"role": "user", "content": message});
    });

    try {
      // Send to backend chat endpoint
      final response = await http.post(
        Uri.parse(
            'http://192.168.1.10:5000/chat'), // Update with your backend URL
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'message': message}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _messages.add({
            "role": "assistant",
            "content": data['answer'] ?? "No response"
          });
        });
      } else {
        setState(() {
          _messages.add({
            "role": "assistant",
            "content":
                "Sorry, I am unable to respond right now. Please try again later."
          });
        });
      }
    } catch (e) {
      setState(() {
        _messages.add({
          "role": "assistant",
          "content":
              "Connection issue detected. Please check your internet connection."
        });
      });
    }

    _controller.clear();
  }

  void _startListening() async {
    bool available = await _speech.initialize(
      onStatus: (val) => print('onStatus: $val'),
      onError: (val) => print('onError: $val'),
    );
    if (available) {
      setState(() => _isListening = true);
      _speech.listen(
        onResult: (val) => setState(() {
          _speechText = val.recognizedWords;
        }),
      );
    }
  }

  void _stopListening() {
    setState(() => _isListening = false);
    _speech.stop();
    if (_speechText.isNotEmpty) {
      _sendMessage(_speechText);
      _speechText = '';
    }
  }

  Future<void> _pickAndUploadImage() async {
    final XFile? image = await _picker.pickImage(source: ImageSource.gallery);
    if (image == null) return;

    setState(() {
      _messages.add({"role": "user", "content": "(Uploaded an image)"});
      _messages.add(
          {"role": "assistant", "content": "Analyzing image, please wait..."});
    });

    final inputImage = InputImage.fromFilePath(image.path);
    final textRecognizer = TextRecognizer(script: TextRecognitionScript.latin);
    final RecognizedText recognizedText =
        await textRecognizer.processImage(inputImage);

    final extractedText = recognizedText.text;

    // Remove the "Analyzing image" message before sending request
    setState(() {
      _messages.removeWhere(
          (msg) => msg['content'] == "Analyzing image, please wait...");
    });

    if (extractedText.isEmpty) {
      setState(() {
        _messages.add(
            {"role": "assistant", "content": "No text detected in the image."});
      });
      return;
    }

    setState(() {
      _messages.add({"role": "user", "content": extractedText});
    });

    try {
      final response = await http.post(
        Uri.parse(
            'http://192.168.1.10:5000/upload_textbook'), // Update with your backend URL
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'text': extractedText}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _messages.add({
            "role": "assistant",
            "content": data['response'] ?? 'No response from server'
          });
        });
      } else {
        setState(() {
          _messages.add({
            "role": "assistant",
            "content": "Failed to analyze textbook content. Please try again."
          });
        });
      }
    } catch (e) {
      setState(() {
        _messages.add({
          "role": "assistant",
          "content":
              "Connection error during image analysis. Please check your internet."
        });
      });
    }
  }

  Future<void> _launchURL(String url) async {
    if (await canLaunch(url)) {
      await launch(url);
    } else {
      throw 'Could not launch $url';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Sahayak - AI Teaching Assistant'),
        actions: [
          IconButton(
            icon: const Icon(Icons.image),
            tooltip: "Upload Textbook Image",
            onPressed: _pickAndUploadImage,
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                return Align(
                  alignment: message['role'] == 'user'
                      ? Alignment.centerRight
                      : Alignment.centerLeft,
                  child: Container(
                    padding:
                        const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
                    margin:
                        const EdgeInsets.symmetric(vertical: 4, horizontal: 16),
                    decoration: BoxDecoration(
                      color: message['role'] == 'user'
                          ? Colors.blue.shade100
                          : Colors.grey.shade100,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: message['role'] == 'user'
                            ? Colors.blue.shade200
                            : Colors.grey.shade300,
                      ),
                    ),
                    child: MarkdownBody(
                      data: message['content'] ?? "No content",
                      styleSheet: MarkdownStyleSheet(
                        p: const TextStyle(color: Colors.black87, fontSize: 14),
                        strong: const TextStyle(fontWeight: FontWeight.bold),
                        em: const TextStyle(fontStyle: FontStyle.italic),
                        a: const TextStyle(
                          color: Colors.blue,
                          decoration: TextDecoration.underline,
                        ),
                      ),
                      onTapLink: (text, href, title) {
                        if (href != null) {
                          _launchURL(href);
                        }
                      },
                    ),
                  ),
                );
              },
            ),
          ),
          Container(
            padding: const EdgeInsets.all(8.0),
            color: Colors.grey.shade50,
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    onSubmitted: (value) {
                      if (value.isNotEmpty) {
                        _sendMessage(value);
                      }
                    },
                    decoration: const InputDecoration(
                      hintText: 'Type your question...',
                      filled: true,
                      fillColor: Colors.white,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.all(Radius.circular(20.0)),
                        borderSide: BorderSide(color: Colors.grey),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.all(Radius.circular(20.0)),
                        borderSide: BorderSide(color: Colors.grey),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  icon: const Icon(Icons.send, color: Colors.deepPurple),
                  onPressed: () {
                    if (_controller.text.isNotEmpty) {
                      _sendMessage(_controller.text);
                    }
                  },
                ),
                IconButton(
                  icon: Icon(
                    _isListening ? Icons.mic : Icons.mic_none,
                    color: _isListening ? Colors.red : Colors.deepPurple,
                  ),
                  onPressed: _isListening ? _stopListening : _startListening,
                ),
                IconButton(
                  icon: const Icon(Icons.photo),
                  tooltip: "Upload Textbook Image",
                  onPressed: _pickAndUploadImage,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ==================== ContentCreationScreen ====================

class ContentCreationScreen extends StatefulWidget {
  const ContentCreationScreen({super.key});

  @override
  _ContentCreationScreenState createState() => _ContentCreationScreenState();
}

class _ContentCreationScreenState extends State<ContentCreationScreen> {
  final _formKey = GlobalKey<FormState>();
  String _contentType = 'story';
  String _topic = '';
  int _gradeLevel = 5;
  String _language = 'English';
  String _region = 'India';
  bool _isGenerating = false;
  String _generatedContent = '';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Content Creation'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: ListView(
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Create Local Educational Content',
                        style: TextStyle(
                            fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 16),
                      DropdownButtonFormField<String>(
                        value: _contentType,
                        decoration: const InputDecoration(
                          labelText: 'Content Type',
                          border: OutlineInputBorder(),
                        ),
                        items: [
                          'story',
                          'poem',
                          'explanation',
                          'activity',
                          'worksheet',
                          'game',
                        ]
                            .map((type) => DropdownMenuItem(
                                  value: type,
                                  child: Text(type.toUpperCase()),
                                ))
                            .toList(),
                        onChanged: (value) =>
                            setState(() => _contentType = value!),
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        decoration: const InputDecoration(
                          labelText: 'Topic',
                          hintText: 'e.g. Water cycle, Fractions, Seasons',
                          border: OutlineInputBorder(),
                        ),
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter a topic';
                          }
                          return null;
                        },
                        onSaved: (value) => _topic = value!,
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: DropdownButtonFormField<int>(
                              value: _gradeLevel,
                              decoration: const InputDecoration(
                                labelText: 'Grade Level',
                                border: OutlineInputBorder(),
                              ),
                              items: List.generate(8, (index) => index + 1)
                                  .map((grade) => DropdownMenuItem(
                                        value: grade,
                                        child: Text('Grade $grade'),
                                      ))
                                  .toList(),
                              onChanged: (value) =>
                                  setState(() => _gradeLevel = value!),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: DropdownButtonFormField<String>(
                              value: _language,
                              decoration: const InputDecoration(
                                labelText: 'Language',
                                border: OutlineInputBorder(),
                              ),
                              items: [
                                'English',
                                'Hindi',
                                'Tamil',
                                'Telugu',
                                'Marathi',
                              ]
                                  .map((lang) => DropdownMenuItem(
                                        value: lang,
                                        child: Text(lang),
                                      ))
                                  .toList(),
                              onChanged: (value) =>
                                  setState(() => _language = value!),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        initialValue: _region,
                        decoration: const InputDecoration(
                          labelText: 'Region',
                          hintText: 'e.g., Maharashtra, Tamil Nadu, Rajasthan',
                          border: OutlineInputBorder(),
                        ),
                        onSaved: (value) => _region = value ?? 'India',
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: _isGenerating ? null : _generateContent,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.deepPurple,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 12),
                          ),
                          child: _isGenerating
                              ? const Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    SizedBox(
                                      width: 20,
                                      height: 20,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        valueColor:
                                            AlwaysStoppedAnimation<Color>(
                                                Colors.white),
                                      ),
                                    ),
                                    SizedBox(width: 8),
                                    Text('Generating...'),
                                  ],
                                )
                              : const Text('Generate Content'),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              if (_generatedContent.isNotEmpty) ...[
                const SizedBox(height: 16),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Generated Content:',
                          style: TextStyle(
                              fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 8),
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.grey.shade50,
                            border: Border.all(color: Colors.grey.shade300),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: MarkdownBody(
                            data: _generatedContent,
                            styleSheet: MarkdownStyleSheet(
                              p: const TextStyle(fontSize: 14, height: 1.5),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  void _generateContent() async {
    if (_formKey.currentState!.validate()) {
      _formKey.currentState!.save();

      setState(() {
        _isGenerating = true;
        _generatedContent = '';
      });

      try {
        final response = await http.post(
          Uri.parse('http://192.168.1.10:5000/generate_content'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'content_type': _contentType,
            'topic': _topic,
            'grade_level': _gradeLevel,
            'language': _language,
            'region': _region,
          }),
        );

        if (response.statusCode == 200) {
          final data = jsonDecode(response.body);
          setState(() {
            _generatedContent = data['content'] ?? 'No content generated';
            _isGenerating = false;
          });
        } else {
          throw Exception('Failed to generate content');
        }
      } catch (e) {
        setState(() {
          _generatedContent = 'Error generating content. Please try again.';
          _isGenerating = false;
        });
      }
    }
  }
}

// ==================== LessonPlannerScreen ====================

class LessonPlannerScreen extends StatelessWidget {
  const LessonPlannerScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Lesson Planner'),
      ),
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.calendar_today, size: 64, color: Colors.deepPurple),
            SizedBox(height: 16),
            Text(
              'Lesson Planning Tool',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 18),
            ),
            SizedBox(height: 8),
            Text(
              'Coming Soon...',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}

// ==================== TextbookAnalyzerScreen ====================

class TextbookAnalyzerScreen extends StatelessWidget {
  const TextbookAnalyzerScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Textbook Helper'),
      ),
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.book, size: 64, color: Colors.deepPurple),
            SizedBox(height: 16),
            Text(
              'Analyze Textbook Pages',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 18),
            ),
            SizedBox(height: 8),
            Text(
              'Coming Soon...',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}

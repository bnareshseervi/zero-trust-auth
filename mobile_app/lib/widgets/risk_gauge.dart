import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../utils/constants.dart';

class RiskGauge extends StatelessWidget {
  final double score;
  final double size;

  const RiskGauge({
    Key? key,
    required this.score,
    this.size = 200,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final color = AppConstants.getRiskColor(score);
    final level = AppConstants.getRiskLevel(score);

    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Background circle
          CustomPaint(
            size: Size(size, size),
            painter: _GaugePainter(
              score: score,
              color: color,
            ),
          ),

          // Center content
          Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                score.toStringAsFixed(0),
                style: TextStyle(
                  fontSize: size * 0.25,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                level,
                style: TextStyle(
                  fontSize: size * 0.08,
                  fontWeight: FontWeight.w600,
                  color: Colors.grey[600],
                  letterSpacing: 1,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                'RISK SCORE',
                style: TextStyle(
                  fontSize: size * 0.06,
                  color: Colors.grey[400],
                  letterSpacing: 0.5,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _GaugePainter extends CustomPainter {
  final double score;
  final Color color;

  _GaugePainter({
    required this.score,
    required this.color,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 20;

    // Background arc
    final backgroundPaint = Paint()
      ..color = Colors.grey[200]!
      ..style = PaintingStyle.stroke
      ..strokeWidth = 20
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      -math.pi * 0.75, // Start angle (top-left)
      math.pi * 1.5, // Sweep angle (270 degrees)
      false,
      backgroundPaint,
    );

    // Foreground arc (colored based on score)
    final foregroundPaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 20
      ..strokeCap = StrokeCap.round;

    final sweepAngle = (score / 100) * math.pi * 1.5;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      -math.pi * 0.75,
      sweepAngle,
      false,
      foregroundPaint,
    );

    // Draw ticks
    _drawTicks(canvas, center, radius);
  }

  void _drawTicks(Canvas canvas, Offset center, double radius) {
    final tickPaint = Paint()
      ..color = Colors.grey[400]!
      ..strokeWidth = 2;

    for (int i = 0; i <= 10; i++) {
      final angle = -math.pi * 0.75 + (i / 10) * math.pi * 1.5;
      final startRadius = radius - 10;
      final endRadius = radius + 10;

      final start = Offset(
        center.dx + startRadius * math.cos(angle),
        center.dy + startRadius * math.sin(angle),
      );

      final end = Offset(
        center.dx + endRadius * math.cos(angle),
        center.dy + endRadius * math.sin(angle),
      );

      canvas.drawLine(start, end, tickPaint);
    }
  }

  @override
  bool shouldRepaint(_GaugePainter oldDelegate) {
    return oldDelegate.score != score || oldDelegate.color != color;
  }
}

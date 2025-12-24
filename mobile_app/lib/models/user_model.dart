class User {
  final int? id; // Made nullable
  final String email;
  final DateTime? createdAt;
  final DateTime? lastLogin;

  User({
    this.id, // Now optional
    required this.email,
    this.createdAt,
    this.lastLogin,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'], // Can be null now
      email: json['email'] ?? 'unknown@example.com',
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'])
          : (json['member_since'] != null
              ? DateTime.tryParse(json['member_since'])
              : null),
      lastLogin: json['last_login'] != null
          ? DateTime.tryParse(json['last_login'])
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'created_at': createdAt?.toIso8601String(),
      'last_login': lastLogin?.toIso8601String(),
    };
  }
}

import boto3
from gtts import gTTS
from pydub import AudioSegment

polly_client = boto3.client("polly")
s3_client = boto3.client("s3")

# Define the conversation
conversation = [
    (
        "Hotel Agent",
        "Good morning! Thank you for calling Sunshine Hotel. My name is Sarah. How may I assist you today?",
    ),
    (
        "Caller",
        "Hi, Sarah. I’m planning a trip next month and wanted to check your room availability and rates.",
    ),
    (
        "Hotel Agent",
        "Certainly! Could you please let me know the dates you’re looking at and the type of room you prefer?",
    ),
    (
        "Caller",
        "Sure, I’m thinking of staying from February 10th to February 14th. I’d prefer a double room with a sea view, if possible.",
    ),
    (
        "Hotel Agent",
        "Let me check that for you. One moment, please. Yes, we do have a double room with a sea view available for those dates. The rate is $150 per night, including breakfast.",
    ),
    ("Caller", "That sounds good. Does the room come with free Wi-Fi and parking?"),
    (
        "Hotel Agent",
        "Yes, all our rooms include complimentary Wi-Fi, and we offer free parking for our guests.",
    ),
    ("Caller", "Perfect! Is there a cancellation policy I should be aware of?"),
    (
        "Hotel Agent",
        "Yes, cancellations are free up to 48 hours before check-in. After that, we charge for one night’s stay.",
    ),
    ("Caller", "Got it. Do you require a deposit to book the room?"),
    (
        "Hotel Agent",
        "We only need your credit card details to secure the booking, but no charges will be made until you arrive.",
    ),
    ("Caller", "Great, let me go ahead and book that."),
    (
        "Hotel Agent",
        "Wonderful! May I have your full name and contact details to proceed with the booking?",
    ),
    ("Caller", "Sure, my name is Mrs. Lara Smith, and my phone number is 555-123-4567."),
    (
        "Hotel Agent",
        "Thank you, Mrs. Smith. Your booking is confirmed for a double room with a sea view from February 10th to February 14th. Is there anything else I can help you with?",
    ),
    ("Caller", "No, that’s all for now. Thank you so much, Sarah!"),
    ("Hotel Agent", "You’re welcome, Mrs. Smith. Have a wonderful day!"),
]

# Create the final combined audio
combined_audio = AudioSegment.silent(duration=0)

for i, (speaker, text) in enumerate(conversation):
    temp_file = f"./temp/temp_{i}.mp3"

    if speaker == "Hotel Agent":
        # Use AWS Polly for this voice
        response = polly_client.synthesize_speech(
            Text=text, OutputFormat="mp3", VoiceId="Joanna"  # Replace with desired Polly voice
        )
        with open(temp_file, "wb") as file:
            file.write(response["AudioStream"].read())
    else:
        # Use gTTS for this voice
        tts = gTTS(text=text, lang="en")
        tts.save(temp_file)

    part_audio = AudioSegment.from_file(temp_file)
    combined_audio += part_audio
    combined_audio += AudioSegment.silent(duration=500)

final_audio_path = "./data/hotel_booking_conversation.mp3"
combined_audio.export(final_audio_path, format="mp3")
print(f"Final audio saved at: {final_audio_path}")

# File details
local_file_path = "./data/hotel_booking_conversation.mp3"
bucket_name = "sentiment-analysis-bucket-dini"
s3_file_key = "audio/hotel_booking_conversation.mp3"

try:
    # Upload file to S3
    s3_client.upload_file(local_file_path, bucket_name, s3_file_key)
    print(f"File successfully uploaded to s3://{bucket_name}/{s3_file_key}")
except Exception as e:
    print(f"Error uploading file: {e}")

# Compiler and flags
CXX = g++
CXXFLAGS = -std=c++17 -O2 -Wall -Wextra -I../lib/rpi-rgb-led-matrix/include

# Linker flags
LDFLAGS = -L../lib/rpi-rgb-led-matrix/lib -lrgbmatrix -lpthread

# Source and object files: only from current directory (no subdirs)
SRCS := $(wildcard *.cc)
OBJS := $(SRCS:.cc=.o)

# Output binary name
TARGET = demo

# Default rule
all: $(TARGET)

# Link all objects into final binary
$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) $^ -o $@ $(LDFLAGS)

# Compile each .cc to .o
%.o: %.cc
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Clean build artifacts
clean:
	rm -f $(OBJS) $(TARGET)

FROM aiidateam/aiida-docker-stack

# Set HOME variable:
ENV HOME="/home/aiida"
ENV RASPA_DIR=${HOME}/code/RASPA2_installed

# Install necessary codes 
RUN apt-get update && apt-get install -y --no-install-recommends  \
    automake \
    libtool


# Copy the current folder and change permissions
COPY . ${HOME}/code/aiida-raspa
RUN chown -R aiida:aiida ${HOME}/code

# Change user to aiida
USER aiida

# Install aiida-raspa plugin and it's dependencies
WORKDIR ${HOME}/code/aiida-raspa
RUN pip install --user .[pre-commit,test]

# Install AiiDA
ENV PATH="${HOME}/.local/bin:${PATH}"

# Download, compile and install RASPA
WORKDIR ${HOME}/code/
RUN git clone https://github.com/iRASPA/RASPA2.git RASPA2
WORKDIR ${HOME}/code/RASPA2
RUN rm -rf autom4te.cache
RUN mkdir m4
RUN aclocal
RUN autoreconf -i
RUN automake --add-missing
RUN autoconf
RUN ./configure --prefix=${RASPA_DIR}
RUN make
RUN make install

# Populate reentry cache for aiida user https://pypi.python.org/pypi/reentry/
RUN reentry scan

# Install the ddec and cp2k codes
COPY .docker/opt/add-codes.sh /opt/
COPY .docker/my_init.d/add-codes.sh /etc/my_init.d/40_add-codes.sh

# Change workdir back to $HOME
WORKDIR ${HOME}

# Important to end as user root!
USER root

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]

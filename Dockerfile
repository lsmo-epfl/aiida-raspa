FROM aiidateam/aiida-docker-stack

# Set HOME, PATH and RASPA_DIR variables:
ENV HOME="/home/aiida"
ENV RASPA2_DIR=${HOME}/code/RASPA2_installed
ENV PATH="/home/aiida/code/RASPA2_installed/bin/:${HOME}/.local/bin:${PATH}"

# Install necessary codes to build RASPA
RUN apt-get update && apt-get install -y --no-install-recommends  \
    automake \
    libtool

# Copy the current folder and change permissions
COPY . ${HOME}/code/aiida-raspa
RUN chown -R aiida:aiida ${HOME}/code

# Now do everything as the aiida user
USER aiida

# Download, compile and install RASPA into ~/code folder
WORKDIR ${HOME}/code/
RUN git clone https://github.com/iRASPA/RASPA2.git RASPA2
WORKDIR ${HOME}/code/RASPA2
RUN rm -rf autom4te.cache
RUN mkdir m4
RUN aclocal
RUN autoreconf -i
RUN automake --add-missing
RUN autoconf
RUN ./configure --prefix=${RASPA2_DIR}
RUN make
RUN make install

# Set the plugin folder as the workdir
WORKDIR ${HOME}/code/aiida-raspa

# Install aiida-raspa plugin and coveralls
RUN pip install --user .[pre-commit,test,docs]
RUN pip install --user coveralls

# Populate reentry cache for aiida user https://pypi.python.org/pypi/reentry/
RUN reentry scan

# Install the RASPA code to AiiDA
COPY .docker/opt/add-codes.sh /opt/
COPY .docker/my_init.d/add-codes.sh /etc/my_init.d/40_add-codes.sh

# Change workdir back to $HOME
WORKDIR ${HOME}

# Important to end as user root!
USER root

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]
